from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_agent_ids(self):

        result = super()._compute_agent_ids()
        for record in self.filtered(
            lambda x: x.move_id.partner_id
            and x.move_id.move_type[:3] == "out"
            and x.product_id
            and not x.agent_ids
        ):
            employee = record.move_id.invoice_user_id.employee_id
            if employee and employee.agent:
                record.agent_ids = [(0, 0, record._prepare_agent_vals(employee))]
        return result
