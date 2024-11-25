from odoo import models, fields, api

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    cashback_percentage = fields.Float(string='Cashback %', digits=(5,2))
    

    @api.onchange('cashback_percentage')
    def _onchange_cashback_percentage(self):
        for line in self.line_ids:
            line.write({
                'cashback_percentage': self.cashback_percentage
            })
            # Memaksa recompute
            line._compute_cashback_values()

    def _create_payments(self):
        # Override method untuk memastikan cashback percentage tersimpan saat pembayaran dibuat
        payments = super()._create_payments()
        
        # Update cashback percentage ke move lines yang terkait
        for payment in payments:
            for line in payment.reconciled_invoice_ids.mapped('invoice_line_ids'):
                line.cashback_percentage = self.cashback_percentage
        
        return payments