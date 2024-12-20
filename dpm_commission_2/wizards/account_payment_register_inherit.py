from odoo import models, fields, api

class AccountPaymentRegisterInherit(models.TransientModel):
    _inherit = 'account.payment.register'
    
    agent_id = fields.Many2one(
        'hr.employee',
        domain=[("agent", "=", True)],
        string='Collector'
    )
    commission_id = fields.Many2one(
        'commission',
        string='Commission',
        domain=['|', ('settlement_type', '=', 'sale_invoice'), ('settlement_type', '=', False)],
    )

    @api.onchange('agent_id')
    def _onchange_agent_id(self):
        if self.agent_id:
            # Cari commission dari agent yang dipilih
            if self.agent_id.commission_id:
                self.commission_id = self.agent_id.commission_id
            else:
                # Jika agent tidak punya commission default, cari commission yang sesuai
                commission = self.env['commission'].search([
                    '|',
                    ('settlement_type', '=', 'sale_invoice'),
                    ('settlement_type', '=', False)
                ], limit=1)
                self.commission_id = commission.id if commission else False
    
    def _create_payments(self):
        payments = super()._create_payments()
        
        if self.agent_id and self.commission_id:
            for payment in payments:
                for move in payment.reconciled_invoice_ids:
                    first_line = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')[:1]
                    if first_line:
                        # Hitung proporsi pembayaran dari total dengan pajak
                        payment_percentage = payment.amount / move.amount_total
                        
                        # Hitung bagian untaxed yang dibayar
                        untaxed_payment = move.amount_untaxed * payment_percentage
                        
                        # Hitung cashback dari untaxed_payment
                        cashback_amount = untaxed_payment * (self.cashback_percentage / 100.0)
                        
                        # paid_amount adalah untaxed_payment dikurangi cashback
                        paid_amount = untaxed_payment - cashback_amount
                        
                        self.env['account.invoice.line.agent'].create({
                            'agent_id': self.agent_id.id,
                            'object_id': first_line.id,
                            'commission_id': self.commission_id.id,
                            'invoice_date': move.invoice_date,
                            'paid_amount': paid_amount
                        })
        return payments
