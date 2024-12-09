from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("order_line.agent_ids.amount")
    def _compute_commission_total(self):
        for record in self:
            record.commission_total = sum(record.mapped("order_line.agent_ids.amount"))

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

    @api.depends("partner_agent_ids", "order_line.agent_ids.agent_id")
    def _compute_agents(self):
        for so in self:
            so.partner_agent_ids = [
                (6, 0, so.mapped("order_line.agent_ids.agent_id").ids)
            ]

    @api.model
    def _search_agents(self, operator, value):
        sol_agents = self.env["sale.order.line.agent"].search(
            [("agent_id", operator, value)]
        )
        return [("id", "in", sol_agents.mapped("object_id.order_id").ids)]

    def recompute_lines_agents(self):
        self.mapped("order_line").recompute_agents()

    def button_edit_sale_agents(self):
        self.ensure_one()
        view = self.env.ref('dpm_commission_2.view_move_agent_form')
        
        # Ambil data komisi yang sudah ada dari sale order line pertama
        first_line = self.order_line.filtered(lambda l: not l.commission_free)[:1]
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
                'default_sale_id': self.id,
                'default_amount_total': self.amount_total,
                'default_line_ids': lines,  # Tambahkan ini untuk menampilkan data existing
            }
        }

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        # Hapus agent_ids dari res karena akan ditangani di invoice line
        if 'agent_ids' in res:
            del res['agent_ids']
        return res


class SaleOrderLine(models.Model):
    _inherit = [
        "sale.order.line",
        "commission.mixin",
    ]
    _name = "sale.order.line"

    agent_ids = fields.One2many(comodel_name="sale.order.line.agent")

    @api.depends("order_id.partner_id")
    def _compute_agent_ids(self):
        self.agent_ids = False  # for resetting previous agents
        for record in self:
            if record.order_id.partner_id and not record.commission_free:
                employee = record.order_id.user_id.employee_id
                if employee and employee.agent:
                    record.agent_ids = [(0, 0, record._prepare_agent_vals(employee))]

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        # Teruskan agent dari sale order line ke invoice line
        if self.agent_ids:
            res['agent_ids'] = [(0, 0, {
                'agent_id': agent.agent_id.id,
                'commission_id': agent.commission_id.id,
            }) for agent in self.agent_ids]
        return res


class SaleOrderLineAgent(models.Model):
    _inherit = "commission.line.mixin"
    _name = "sale.order.line.agent"

    object_id = fields.Many2one(comodel_name="sale.order.line")

    agent_id = fields.Many2one(
        comodel_name="hr.employee",
        domain=[("agent", "=", True)],
        required=True,
    )

    @api.depends(
        "commission_id",
        "object_id.price_subtotal",
        "object_id.product_id",
        "object_id.product_uom_qty",
    )
    def _compute_amount(self):
        for line in self:
            order_line = line.object_id
            line.amount = line._get_commission_amount(
                line.commission_id,
                order_line.price_subtotal,
                order_line.product_id,
                order_line.product_uom_qty,
            )