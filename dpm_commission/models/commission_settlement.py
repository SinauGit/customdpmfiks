from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import groupby


class CommissionSettlement(models.Model):
    _name = "commission.settlement"
    _description = "Settlement"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char()
    total = fields.Float(compute="_compute_total", readonly=True, store=True)
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    agent_id = fields.Many2one(
        comodel_name="hr.employee",
        domain="[('agent', '=', True)]",
        required=True,
        string="Salesperson",
    )
    agent_type = fields.Selection(related="agent_id.agent_type")

    settlement_type = fields.Selection(
        selection=[("sale_invoice", "Sales Invoices")],
        default="sale_invoice",
        readonly=True,
        required=True,
    )

    # settlement_type = fields.Selection(
    #     selection=[("manual", "Manual")],
    #     default="manual",
    #     readonly=True,
    #     required=True,
    # )
    can_edit = fields.Boolean(
        compute="_compute_can_edit",
        store=True,
    )
    line_ids = fields.One2many(
        comodel_name="commission.settlement.line",
        inverse_name="settlement_id",
        string="Settlement lines",
    )
    state = fields.Selection(
        selection=[
            ("settled", "Settled"),
            ("cancel", "Canceled"),
        ],
        readonly=True,
        required=True,
        default="settled",
        string ="Status",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        readonly=True,
        default=lambda self: self._default_currency_id(),
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self._default_company_id(),
        required=True,
    )

    def _default_currency_id(self):
        return self.env.company.currency_id.id

    def _default_company_id(self):
        return self.env.company.id

    @api.depends("line_ids", "line_ids.settled_amount")
    def _compute_total(self):
        for record in self:
            record.total = sum(record.mapped("line_ids.settled_amount"))

    @api.depends("settlement_type")
    def _compute_can_edit(self):
        for record in self:
            record.can_edit = False

    # @api.depends("settlement_type")
    # def _compute_can_edit(self):
    #     for record in self:
    #         record.can_edit = record.settlement_type == "manual"

    def action_cancel(self):
        self.write({"state": "cancel"})

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super()._message_auto_subscribe_followers(updated_values, subtype_ids)
        if updated_values.get("agent_id"):
            res.append((updated_values["agent_id"], subtype_ids, False))
        return res

    def unlink(self):
        if any(x.state == "invoiced" for x in self):
            raise UserError(_("You can't delete invoiced settlements."))
        
        # Hapus followers terlebih dahulu
        self.env['mail.followers'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids)
        ]).unlink()
        
        return super().unlink()


class SettlementLine(models.Model):
    _name = "commission.settlement.line"
    _description = "Line of a commission settlement"

    settlement_id = fields.Many2one(
        "commission.settlement",
        readonly=True,
        ondelete="cascade",
        required=True,
    )
    date = fields.Date(
        compute="_compute_date",
        readonly=False,
        store=True,
        required=True,
    )
    agent_id = fields.Many2one(
        comodel_name="hr.employee",
        related="settlement_id.agent_id",
        store=True,
    )
    settled_amount = fields.Monetary(
        compute="_compute_settled_amount", readonly=False, store=True
    )
    currency_id = fields.Many2one(
        related="settlement_id.currency_id",
        comodel_name="res.currency",
        store=True,
        readonly=True,
    )
    commission_id = fields.Many2one(
        comodel_name="commission",
        compute="_compute_commission_id",
        readonly=False,
        store=True,
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="settlement_id.company_id",
        store=True,
    )

    def _compute_date(self):
        """
        """

    def _compute_commission_id(self):
        """
        """

    def _compute_settled_amount(self):
        """
        """