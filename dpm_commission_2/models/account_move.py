from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"
    
    commission_total = fields.Float(
        string="Commissions",
        compute="_compute_commission_total",
        store=True,
    )
    partner_agent_ids = fields.Many2many(
        string="Sales Teams",
        comodel_name="hr.employee",
        compute="_compute_agents",
        search="_search_agents",
    )
    settlement_count = fields.Integer(compute="_compute_settlement")
    settlement_ids = fields.One2many(
        "commission.settlement",
        string="Settlements",
        compute="_compute_settlement",
    )

    def action_view_settlement(self):
        xmlid = "dpm_commission.action_commission_settlement"
        action = self.env["ir.actions.actions"]._for_xml_id(xmlid)
        action["context"] = {}
        settlements = self.mapped("settlement_ids")
        if not settlements or len(settlements) > 1:
            action["domain"] = [("id", "in", settlements.ids)]
        elif len(settlements) == 1:
            res = self.env.ref("dpm_commission.view_settlement_form", False)
            action["views"] = [(res and res.id or False, "form")]
            action["res_id"] = settlements.id
        return action

    def _compute_settlement(self):
        for invoice in self:
            settlements = invoice.invoice_line_ids.settlement_id
            invoice.settlement_ids = settlements
            invoice.settlement_count = len(settlements)

    @api.depends("partner_agent_ids", "invoice_line_ids.agent_ids.agent_id")
    def _compute_agents(self):
        for move in self:
            move.partner_agent_ids = [
                (6, 0, move.mapped("invoice_line_ids.agent_ids.agent_id").ids)
            ]

    @api.model
    def _search_agents(self, operator, value):
        ail_agents = self.env["account.invoice.line.agent"].search(
            [("agent_id", operator, value)]
        )
        return [("id", "in", ail_agents.mapped("object_id.move_id").ids)]

    @api.depends("line_ids.agent_ids.amount")
    def _compute_commission_total(self):
        for record in self:
            record.commission_total = 0.0
            for line in record.line_ids:
                record.commission_total += sum(x.amount for x in line.agent_ids)

    def action_post(self):

        self.mapped("line_ids.settlement_id").write({"state": "invoiced"})
        return super().action_post()

    def button_cancel(self):

        if any(self.mapped("invoice_line_ids.any_settled")):
            raise exceptions.ValidationError(
                _("You can't cancel an invoice with settled lines"),
            )
        self.mapped("line_ids.settlement_id").write({"state": "except_invoice"})
        return super().button_cancel()

    def recompute_lines_agents(self):
        self.mapped("invoice_line_ids").recompute_agents()

    def unlink(self):

        self.invoice_line_ids.settlement_id.filtered(
            lambda s: s.state == "invoiced"
        ).write({"state": "settled"})
        return super().unlink()
    
    def action_post(self):
        super().action_post()
        self._check_and_update_settlement_state()

    def _check_and_update_settlement_state(self):
        for move in self:
            if move.state == "posted":
                settlements = move.mapped("line_ids.settlement_id")
                settlements.write({"state": "paid"})


    def button_edit_move_agents(self):
        self.ensure_one()
        view = self.env.ref('dpm_commission_2.view_move_agent_form')
        
        # Ambil data komisi yang sudah ada dari invoice line pertama
        first_line = self.invoice_line_ids.filtered(lambda l: l.display_type == 'product')[:1]
        lines = []
        if first_line and first_line.agent_ids:
            for agent in first_line.agent_ids:
                lines.append((0, 0, {
                    'agent_id': agent.agent_id.id,
                    'commission_id': agent.commission_id.id,
                }))
                
        return {
            'name': _('Sales Teams'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move.agent.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_amount_total': self.amount_total,
                'default_line_ids': lines,  # Tambahkan ini untuk menampilkan data existing
            }
        }

    # Override method button_draft untuk menghapus collector sebelum reset ke draft

    def button_draft(self):
        # Override method button_draft untuk menghapus collector sebelum reset ke draft
        for move in self:
            # Hapus followers terlebih dahulu
            self.env['mail.followers'].sudo().search([
                ('res_model', '=', self._name),
                ('res_id', '=', move.id)
            ]).unlink()
            
            # Cari agent collector di invoice lines
            collector_agents = move.invoice_line_ids.mapped('agent_ids').filtered(
                lambda x: x.commission_id.name == 'Collector'
            )
            if collector_agents:
                # Hapus settlement lines terkait collector
                collector_agents.mapped('settlement_line_ids').unlink()
                # Hapus agent collector
                collector_agents.unlink()
                
            # Reset paid_amount di invoice lines
            for line in move.invoice_line_ids:
                if hasattr(line, 'paid_amount'):
                    line.paid_amount = 0.0

        return super().button_draft()


class AccountMoveLine(models.Model):
    _inherit = [
        "account.move.line",
        "commission.mixin",
    ]
    _name = "account.move.line"

    agent_ids = fields.One2many(comodel_name="account.invoice.line.agent")
    any_settled = fields.Boolean(compute="_compute_any_settled")

    settlement_id = fields.Many2one(
        comodel_name="commission.settlement",
        copy=False,
    )

    @api.depends("agent_ids", "agent_ids.settled")
    def _compute_any_settled(self):
        for record in self:
            record.any_settled = any(record.mapped("agent_ids.settled"))

    @api.depends("move_id.partner_id")
    def _compute_agent_ids(self):
        self.agent_ids = False  # for resetting previous agents
        for record in self:
            if (
                record.move_id.partner_id
                and record.move_id.move_type[:3] == "out"
                and not record.commission_free
                and record.product_id
            ):
                record.agent_ids = record._prepare_agents_vals_partner(
                    record.move_id.partner_id, settlement_type="sale_invoice"
                )

    def _copy_data_extend_business_fields(self, values):

        res = super()._copy_data_extend_business_fields(values)
        if self.settlement_id and self.env.context.get("include_settlement", False):
            values["settlement_id"] = self.settlement_id.id
        return res


class AccountInvoiceLineAgent(models.Model):
    _inherit = "commission.line.mixin"
    _name = "account.invoice.line.agent"
    _description = "Agent detail of commission line in invoice lines"

    object_id = fields.Many2one(comodel_name="account.move.line")
    invoice_id = fields.Many2one(
        string="Invoice",
        comodel_name="account.move",
        related="object_id.move_id",
        store=True,
    )
    invoice_date = fields.Date(
        string="Invoice date",
        related="invoice_id.invoice_date",
        store=True,
        readonly=True,
    )
    settlement_line_ids = fields.One2many(
        comodel_name="commission.settlement.line",
        inverse_name="invoice_agent_line_id",
    )
    settled = fields.Boolean(compute="_compute_settled", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_company",
        store=True,
    )
    currency_id = fields.Many2one(
        related="object_id.currency_id",
    )
    invoice_display_name = fields.Char(
        string="Invoice Number",
        related="invoice_id.name",
        store=True,
    )

    @api.depends(
        "object_id.price_subtotal",
        "object_id.commission_free",
        "commission_id",
    )
    def _compute_amount(self):
        for line in self:
            inv_line = line.object_id
            line.amount = line._get_commission_amount(
                line.commission_id,
                inv_line.price_subtotal,
                inv_line.product_id,
                inv_line.quantity,
            )
            # Refunds commissions are negative
            if line.invoice_id.move_type and "refund" in line.invoice_id.move_type:
                line.amount = -line.amount

    @api.depends(
        "settlement_line_ids",
        "settlement_line_ids.settlement_id.state",
        "invoice_id",
        "invoice_id.state",
    )
    def _compute_settled(self):
        # Count lines of not open or paid invoices as settled for not
        # being included in settlements
        for line in self:
            line.settled = any(
                x.settlement_id.state != "cancel" for x in line.settlement_line_ids
            )

    @api.depends("object_id", "object_id.company_id")
    def _compute_company(self):
        for line in self:
            line.company_id = line.object_id.company_id

    @api.constrains("agent_id", "amount")
    def _check_settle_integrity(self):
        for record in self:
            if any(record.mapped("settled")):
                raise exceptions.ValidationError(
                    _("You can't modify a settled line"),
                )

    def _skip_settlement(self):

        self.ensure_one()
        return (
            self.commission_id.invoice_state == "paid"
            and self.invoice_id.payment_state not in ["in_payment", "paid", "reversed"]
        ) or self.invoice_id.state != "posted"
