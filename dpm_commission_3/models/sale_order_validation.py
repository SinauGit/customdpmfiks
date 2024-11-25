from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            # Cek hanya line pertama yang tidak commission_free
            first_line = order.order_line.filtered(lambda l: l.product_id and not l.commission_free)[:1]
            if first_line and not first_line.agent_ids:
                raise ValidationError(_(
                    'Please set commission first before confirm the quotation.\n'
                    'You can set it by clicking the "Edit Commission" button'
                ))
        return super().action_confirm()