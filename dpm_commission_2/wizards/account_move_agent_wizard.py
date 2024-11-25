from odoo import models, fields, api

class AccountMoveAgentWizard(models.TransientModel):
    _name = 'account.move.agent.wizard'
    _description = 'Account Move Agent Wizard'

    move_id = fields.Many2one('account.move', string='Invoice')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    amount_total = fields.Float(string='Amount', readonly=True)
    line_ids = fields.One2many(
        'account.move.agent.wizard.line',
        'wizard_id',
        string='Lines'
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'move_id' in res:
            move = self.env['account.move'].browse(res['move_id'])
            first_line = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')[:1]
            if first_line and first_line.agent_ids:
                lines = []
                for agent in first_line.agent_ids:
                    lines.append((0, 0, {
                        'agent_id': agent.agent_id.id,
                        'commission_id': agent.commission_id.id,
                    }))
                res['line_ids'] = lines
        elif 'sale_id' in res:
            sale = self.env['sale.order'].browse(res['sale_id'])
            first_line = sale.order_line.filtered(lambda l: not l.commission_free)[:1]
            if first_line and first_line.agent_ids:
                lines = []
                for agent in first_line.agent_ids:
                    lines.append((0, 0, {
                        'agent_id': agent.agent_id.id,
                        'commission_id': agent.commission_id.id,
                    }))
                res['line_ids'] = lines
        return res

    def action_apply(self):
        self.ensure_one()
        if self.move_id:
            first_line = self.move_id.invoice_line_ids.filtered(lambda l: l.display_type == 'product')[:1]
            if first_line:
                first_line.agent_ids.unlink()
                for line in self.line_ids:
                    self.env['account.invoice.line.agent'].create({
                        'agent_id': line.agent_id.id,
                        'object_id': first_line.id,
                        'commission_id': line.commission_id.id,
                    })
        elif self.sale_id:
            first_line = self.sale_id.order_line.filtered(lambda l: not l.commission_free)[:1]
            if first_line:
                first_line.agent_ids.unlink()
                for line in self.line_ids:
                    self.env['sale.order.line.agent'].create({
                        'agent_id': line.agent_id.id,
                        'object_id': first_line.id,
                        'commission_id': line.commission_id.id,
                    })
        return {'type': 'ir.actions.act_window_close'}

class AccountMoveAgentWizardLine(models.TransientModel):
    _name = 'account.move.agent.wizard.line'
    _description = 'Account Move Agent Wizard Line'

    wizard_id = fields.Many2one('account.move.agent.wizard', string='Wizard')
    agent_id = fields.Many2one(
        'res.partner',
        string='Salesperson',
        domain=[('agent', '=', True)],
        required=True
    )
    commission_id = fields.Many2one(
        'commission',
        string='Commission',
        domain=['|', ('settlement_type', '=', 'sale_invoice'), ('settlement_type', '=', False)],
        required=True
    )

    @api.onchange('agent_id')
    def _onchange_agent_id(self):
        if self.agent_id and self.agent_id.commission_id:
            self.commission_id = self.agent_id.commission_id
