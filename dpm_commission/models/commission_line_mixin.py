from odoo import fields, models, api

class CommissionLineMixin(models.Model):
    _name = "commission.line.mixin"
    _description = "Commission Line Mixin"
    
    agent_id = fields.Many2one(
        comodel_name="hr.employee",
        domain=[("agent", "=", True)],
        required=True,
    )
    commission_id = fields.Many2one(
        comodel_name="commission",
        required=True,
    )
    amount = fields.Float(
        compute="_compute_amount",
        store=True,
    )
    object_id = fields.Reference(
        selection=[
            ('sale.order.line', 'Sale Order Line'),
            ('account.move.line', 'Invoice Line'),
        ],
        required=True,
        ondelete='cascade',
    )

    @api.depends("commission_id")
    def _compute_amount(self):
        for line in self:
            line.amount = 0.0 