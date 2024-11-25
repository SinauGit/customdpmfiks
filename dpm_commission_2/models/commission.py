from odoo import fields, models


class Commission(models.Model):
    _inherit = "commission"

    invoice_state = fields.Selection(
        [
        # ("open", "Invoice Based"), 
        ("paid", "Payment Based")
        ],
        string="Invoice Status",
        default="paid",
    )
