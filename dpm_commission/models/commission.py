from odoo import _, api, exceptions, fields, models


class Commission(models.Model):
    _name = "commission"
    _description = "Commission"

    name = fields.Char(required=True)
    commission_type = fields.Selection(
        selection=[("fixed", "Fixed percentage"), 
                   ("section", "By Interval Amount")
                   ],
        string="Type",
        required=True,
        default="fixed",

    )
    rate_1 = fields.Float(string="0-6 Months")
    rate_2 = fields.Float(string="7 - 12 Months")
    section_ids = fields.One2many(
        string="Sections",
        comodel_name="commission.section",
        inverse_name="commission_id",
    )
    active = fields.Boolean(default=True)
    amount_base_type = fields.Selection(
        selection=[
            ("gross_amount", "Sale/Invoice Amount"),
            # ("net_amount", "Margin (Amount - Cost)"),
        ],
        string="Base",
        required=True,
        default ="gross_amount",
    )
    settlement_type = fields.Selection(selection="_selection_settlement_type")
    additional_commission = fields.Float(string="Additional Commission")

    @api.model
    def _selection_settlement_type(self):

        return self.env["commission.settlement"].fields_get(
            allfields=["settlement_type"]
        )["settlement_type"]["selection"]

    def calculate_section(self, base):
        self.ensure_one()
        for section in self.section_ids:
            if section.amount_from <= base <= section.amount_to:
                return base * section.percent / 100.0
        return 0.0


class CommissionSection(models.Model):
    _name = "commission.section"
    _description = "Commission section"

    commission_id = fields.Many2one("commission", string="Commission")
    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    percent = fields.Float(required=True)

    @api.constrains("amount_from", "amount_to")
    def _check_amounts(self):
        for section in self:
            if section.amount_to < section.amount_from:
                raise exceptions.ValidationError(
                    _("The lower limit cannot be greater than upper one.")
                )
