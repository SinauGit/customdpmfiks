from datetime import date, timedelta
from itertools import groupby

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class CommissionMakeSettle(models.TransientModel):
    _name = "commission.make.settle"

    date_to = fields.Date("Up to", required=True, default=fields.Date.today)
    agent_ids = fields.Many2many(
        comodel_name="res.partner", domain="[('agent', '=', True)]"
    )
    settlement_type = fields.Selection(
        selection=[
            ('sale_invoice', 'Sale Invoice'),
        ],
        required=True,
        default="sale_invoice"
    )
    can_settle = fields.Boolean(
        compute="_compute_can_settle",
    )

    @api.depends("date_to")  # use this unrelated field to trigger the computation
    def _compute_can_settle(self):
        self.can_settle = bool(
            self.env[self._name]._fields["settlement_type"].selection
        )

    def _get_period_start(self, agent, date_to):
        if agent.settlement == "monthly":
            return date(month=date_to.month, year=date_to.year, day=1)
        elif agent.settlement == "biweekly":
            if date_to.day >= 16:
                return date(month=date_to.month, year=date_to.year, day=16)
            else:
                return date(month=date_to.month, year=date_to.year, day=1)
        elif agent.settlement == "quaterly":
            # Get first month of the date quarter
            month = (date_to.month - 1) // 3 * 3 + 1
            return date(month=month, year=date_to.year, day=1)
        elif agent.settlement == "semi":
            if date_to.month > 6:
                return date(month=7, year=date_to.year, day=1)
            else:
                return date(month=1, year=date_to.year, day=1)
        elif agent.settlement == "annual":
            return date(month=1, year=date_to.year, day=1)
        elif agent.settlement == "6_months_ago":
            # Tanggal mulai adalah akhir bulan dari 6 bulan yang lalu
            six_months_ago = date_to - relativedelta(months=6)
            last_day_of_six_months_ago = date(
                year=six_months_ago.year,
                month=six_months_ago.month,
                day=1
            ) + relativedelta(months=1, days=-1)
            return last_day_of_six_months_ago

    def _get_next_period_date(self, agent, current_date):
        if agent.settlement == "monthly":
            return current_date + relativedelta(months=1)
        elif agent.settlement == "biweekly":
            if current_date.day == 1:
                return current_date + relativedelta(days=15)
            else:
                return date(
                    month=current_date.month, year=current_date.year, day=1
                ) + relativedelta(months=1, days=-1)
        elif agent.settlement == "quaterly":
            return current_date + relativedelta(months=3)
        elif agent.settlement == "semi":
            return current_date + relativedelta(months=6)
        elif agent.settlement == "annual":
            return current_date + relativedelta(years=1)
        elif agent.settlement == "6_months_ago":
            # Menggunakan tanggal yang sama 1 tahun sebelumnya
            one_year_ago = self.date_to - relativedelta(years=1)
            return one_year_ago

    def _get_settlement(self, agent, company, currency, sett_from, sett_to):
        self.ensure_one()
        return self.env["commission.settlement"].search(
            [
                ("agent_id", "=", agent.id),
                ("date_from", "=", sett_from),
                ("date_to", "=", sett_to),
                ("company_id", "=", company.id),
                ("currency_id", "=", currency.id),
                ("state", "=", "settled"),
                ("settlement_type", "=", self.settlement_type), 
            ],
            limit=1,
        )

    def _prepare_settlement_vals(self, agent, company, sett_from, sett_to):
        # Menentukan nama settlement
        settlement_name = f"Settlement {agent.name}"

        return {
            "name": settlement_name,
            "agent_id": agent.id,
            "date_from": sett_from,
            "date_to": sett_to,
            "company_id": company.id,
            "settlement_type": self.settlement_type,
        }

    def _prepare_settlement_line_vals(self, settlement, line):
        """Hook for returning the settlement line dictionary vals."""
        return {
            "settlement_id": settlement.id,
        }

    def _get_agent_lines(self, date_to_agent):
        raise NotImplementedError()

    @api.model
    def _agent_lines_groupby(self, agent_line):
        return agent_line.company_id, agent_line.currency_id

    @api.model
    def _agent_lines_sorted(self, agent_line):
        return agent_line.company_id.id, agent_line.currency_id.id

    def action_settle(self):
        self.ensure_one()
        settlement_obj = self.env["commission.settlement"]
        settlement_line_obj = self.env["commission.settlement.line"]
        settlement_ids = []
        
        # Ambil semua agents dari line
        agents = self.agent_ids or self.env["res.partner"].search([("agent", "=", True)])
        date_to = self.date_to
        
        for agent in agents:
            date_to_agent = self._get_period_start(agent, date_to)
            # Get non settled elements
            grouped_agent_lines = groupby(
                sorted(
                    self._get_agent_lines(agent, date_to_agent),
                    key=self._agent_lines_sorted,
                ),
                key=self._agent_lines_groupby,
            )
            
            for _k, grouper_agent_lines in grouped_agent_lines:
                agent_lines = list(grouper_agent_lines)
                pos = 0
                sett_to = date(year=1900, month=1, day=1)
                settlement_line_vals = []
                
                while pos < len(agent_lines):
                    line = agent_lines[pos]
                    pos += 1
                    if line._skip_settlement():
                        continue
                        
                    # Tanggal untuk perhitungan rate
                    six_months_ago = date_to - relativedelta(months=6)
                    last_day_of_six_months_ago = date(
                        year=six_months_ago.year,
                        month=six_months_ago.month,
                        day=1
                    ) + relativedelta(months=1, days=-1)
                    
                    # Perubahan di sini - menggunakan tanggal yang sama 1 tahun sebelumnya
                    one_year_ago = date_to - relativedelta(years=1)
                    first_day_of_one_year_ago = one_year_ago
                    
                    # Khusus untuk collector, gunakan paid_amount
                    if line.commission_id.name == 'Collector':
                        if line.invoice_date.month == six_months_ago.month and line.invoice_date.year == six_months_ago.year:
                            total_rate1 = line.commission_id.rate_1 + line.commission_id.additional_commission
                            line.amount = line.paid_amount * (total_rate1 / 100.0)
                        elif first_day_of_one_year_ago <= line.invoice_date < last_day_of_six_months_ago:
                            total_rate2 = line.commission_id.rate_2 + line.commission_id.additional_commission
                            line.amount = line.paid_amount * (total_rate2 / 100.0)
                        else:
                            continue
                    else:
                        # Untuk non-collector, gunakan perhitungan normal
                        if line.invoice_date.month == six_months_ago.month and line.invoice_date.year == six_months_ago.year:
                            total_rate1 = line.commission_id.rate_1 + line.commission_id.additional_commission
                            line.amount = line.object_id.price_after_cashback * (total_rate1 / 100.0)
                        elif first_day_of_one_year_ago <= line.invoice_date < last_day_of_six_months_ago:
                            total_rate2 = line.commission_id.rate_2 + line.commission_id.additional_commission
                            line.amount = line.object_id.price_after_cashback * (total_rate2 / 100.0)
                        else:
                            continue
                        
                    # Buat settlement
                    if line.invoice_date > sett_to:
                        sett_from = self._get_period_start(agent, line.invoice_date)
                        sett_to = self._get_next_period_date(agent, sett_from)
                        sett_to -= timedelta(days=1)
                        settlement = self._get_settlement(
                            agent, line.company_id, line.currency_id, sett_from, sett_to
                        )
                        if not settlement:
                            settlement = settlement_obj.create(
                                self._prepare_settlement_vals(
                                    agent,
                                    line.company_id,
                                    sett_from,
                                    sett_to,
                                )
                            )
                            settlement.currency_id = line.currency_id
                        settlement_ids.append(settlement.id)
                    settlement_line_vals.append(
                        self._prepare_settlement_line_vals(settlement, line)
                    )
                settlement_line_obj.create(settlement_line_vals)
        # go to results
        if len(settlement_ids):
            return {
                "name": _("Created Settlements"),
                "type": "ir.actions.act_window",
                "views": [[False, "list"], [False, "form"]],
                "res_model": "commission.settlement",
                "domain": [["id", "in", settlement_ids]],
            }


