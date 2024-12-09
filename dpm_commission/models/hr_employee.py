from odoo import api, fields, models

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    agent = fields.Boolean(
        string="Sales Teams",
    )
    agent_type = fields.Selection(
        selection=[("agent", "Internal Salesperson")],
        string="Type",
        default="agent",
    )
    commission_id = fields.Many2one(
        string="Commission",
        comodel_name="commission",
    )
    settlement = fields.Selection(
        selection=[
            ("6_months_ago", "6 months ago"),
        ],
        string="Settlement period",
        default="6_months_ago",
    )
    settlement_ids = fields.One2many(
        comodel_name="commission.settlement",
        inverse_name="agent_id",
        readonly=True,
    ) 