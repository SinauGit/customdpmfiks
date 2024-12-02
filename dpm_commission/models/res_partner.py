from odoo import api, fields, models


class ResPartner(models.Model):


    _inherit = "res.partner"

    agent_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="partner_agent_rel",
        column1="partner_id",
        column2="agent_id",
        domain=[("agent", "=", True)],
        readonly=False,
        string="Sales Teams",
    )

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
            # ("biweekly", "Bi-weekly"),
            # ("monthly", "Monthly"),
            # ("quaterly", "Quarterly"),
            # ("semi", "Semi-annual"),
            # ("annual", "Annual"),
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

    @api.model
    def _commercial_fields(self):

        res = super()._commercial_fields()
        res.append("agent_ids")
        return res
