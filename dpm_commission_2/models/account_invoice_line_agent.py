from odoo import models, fields

class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    paid_amount = fields.Float(
        string='Paid Amount',
        help='Amount collected by collector'
    ) 