from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    # def action_post(self):
    #     for move in self:
    #         first_line = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')[:1]
    #         if first_line and not first_line.commission_free and not first_line.agent_ids:
    #             raise ValidationError(_(
    #                 'Please set commission first before confirm the invoice.\n'
    #                 'You can set it by clicking the "Edit Commission" button'
    #             ))
    #     return super().action_post()