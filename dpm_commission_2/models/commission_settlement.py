from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import groupby


class CommissionSettlement(models.Model):
    _inherit = "commission.settlement"

    settlement_type = fields.Selection(
        selection_add=[("sale_invoice", "Sales Invoices")],
        ondelete={"sale_invoice": "set default"},
    )
    state = fields.Selection(
        selection_add=[
            ("invoiced", "Invoiced"),
            ("except_invoice", "Payment Exception"),
            ("paid", "Paid"),  # Tambahkan state "Paid"
        ],
        ondelete={"invoiced": "set default", "except_invoice": "set default", "paid": "set default"},
    )
    
    invoice_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="settlement_id",
        string="Generated invoice lines",
        readonly=True,
    )
    invoice_id = fields.Many2one(
        string="Generated Invoice",
        store=True,
        comodel_name="account.move",
        compute="_compute_invoice_id",
    )
    invoice_count = fields.Integer(
        string="# of Invoices",
        compute='_compute_invoice_count',
    )

    def _compute_can_edit(self):

        sale_invoices = self.filtered(lambda x: x.settlement_type == "sale_invoice")
        sale_invoices.update({"can_edit": False})
        return super(CommissionSettlement, self - sale_invoices)._compute_can_edit()

    @api.depends("invoice_line_ids")
    def _compute_invoice_id(self):
        for record in self:
            record.invoice_id = record.invoice_line_ids.filtered(
                lambda x: x.parent_state != "cancel"
            )[:1].move_id

    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_id) if record.invoice_id else 0

    def action_cancel(self):

        if any(x.state != "settled" for x in self):
            raise UserError(_("Cannot cancel an invoiced settlement."))
        return super().action_cancel()

    def action_draft(self):
        self.write({"state": "settled"})

    def unlink(self):

        if any(x.state == "invoiced" for x in self):
            raise UserError(_("You can't delete invoiced settlements."))
        return super().unlink()

    def action_invoice(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Make invoice"),
            "res_model": "commission.make.invoice",
            "target": "new",
            "view_mode": "form",
            "context": {"settlement_ids": self.ids},
        }

    def _get_invoice_partner(self):
        """Override untuk menggunakan employee"""
        employee = fields.first(self).agent_id
        return self.env['res.partner'].search([
            ('name', '=', employee.name)
        ], limit=1) or self.env.company.partner_id

    def _prepare_invoice(self, journal, product, date=False):
        partner = self._get_invoice_partner()
        vals = {
            "move_type": "in_invoice",
            "partner_id": partner.id,
            "journal_id": journal.id,
            "invoice_line_ids": [],
            "currency_id": self.currency_id.id,
        }
        if date:
            vals.update({"invoice_date": date})
        for settlement in self:
            # Get first settlement line date
            first_line = settlement.line_ids[:1]
            if first_line and first_line.date:
                # Format bulan dan tahun dari tanggal settlement line pertama
                date_str = first_line.date.strftime('%B %Y')  # Contoh: "December 2023"
                description = f"Commission {date_str}"
            else:
                description = product.with_context(lang=lang.code).display_name

            vals["invoice_line_ids"].append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "quantity": -1 if settlement.total < 0 else 1,
                        "price_unit": abs(settlement.total),
                        "name": description,  # Gunakan description yang baru
                        "currency_id": settlement.currency_id.id,
                        "settlement_id": settlement.id,
                    },
                )
            )
        return vals

    def _get_invoice_grouping_keys(self):
        return ["company_id", "currency_id", "agent_id"]

    def make_invoices(self, journal, product, date=False, grouped=False):
        invoice_vals_list = []
        settlement_obj = self.env[self._name]
        if grouped:
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            settlements = groupby(
                self.sorted(
                    key=lambda x: [
                        x._fields[grouping_key].convert_to_write(x[grouping_key], x)
                        for grouping_key in invoice_grouping_keys
                    ],
                ),
                key=lambda x: tuple(
                    x._fields[grouping_key].convert_to_write(x[grouping_key], x)
                    for grouping_key in invoice_grouping_keys
                ),
            )
            grouped_settlements = [
                settlement_obj.union(*list(sett))
                for _grouping_keys, sett in settlements
            ]
        else:
            grouped_settlements = self
        for settlement in grouped_settlements:
            invoice_vals = settlement._prepare_invoice(journal, product, date)
            invoice_vals_list.append(invoice_vals)
        invoices = self.env["account.move"].create(invoice_vals_list)
        invoices.sudo().filtered(lambda m: m.amount_total < 0).with_context(
            include_settlement=True
        ).action_switch_move_type()
        self.write({"state": "invoiced"})
        return invoices

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        if len(self.invoice_id) > 1:
            action["domain"] = [("id", "in", self.invoice_id.ids)]
        else:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            action["views"] = form_view
            action["res_id"] = self.invoice_id.id
        return action


class SettlementLine(models.Model):
    _inherit = "commission.settlement.line"

    invoice_agent_line_id = fields.Many2one(comodel_name="account.invoice.line.agent")
    invoice_line_id = fields.Many2one(
        comodel_name="account.move.line",
        store=True,
        related="invoice_agent_line_id.object_id",
        string="Source invoice line",
    )
    invoice_number = fields.Char(
        string="Invoice Number",
        related="invoice_agent_line_id.invoice_display_name",
        store=True,
    )

    @api.depends("invoice_agent_line_id")
    def _compute_date(self):
        for record in self:
            if not record.invoice_agent_line_id:
                continue
            record.date = record.invoice_agent_line_id.invoice_date

    @api.depends("invoice_agent_line_id")
    def _compute_commission_id(self):
        for record in self:
            if not record.invoice_agent_line_id:
                continue
            record.commission_id = record.invoice_agent_line_id.commission_id

    @api.depends("invoice_agent_line_id")
    def _compute_settled_amount(self):
        for record in self:
            if not record.invoice_agent_line_id:
                continue
            record.settled_amount = record.invoice_agent_line_id.amount
