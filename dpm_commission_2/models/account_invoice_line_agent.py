from odoo import models, fields

class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    agent_id = fields.Many2one(
        comodel_name="hr.employee",
        domain=[("agent", "=", True)],
        required=True,
    )
    paid_amount = fields.Float(
        string='Paid Amount',
        help='Amount collected by collector'
    ) 