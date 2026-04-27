# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _load(self, company):
        self.ensure_one()
        super()._load(company)

        # Set default accounts for company
        chart_template = self.env.ref("l10n_br_coa_eiras.account_template_eiras")
        if self.id == chart_template.id:
            suspense_account_id = self.env["account.account"].search(
                [("code", "=", "1.1.1.03.9001"), ("company_id", "=", company.id)],
                limit=1,
            )
            company.write(
                {"account_journal_suspense_account_id": suspense_account_id.id}
            )

        return {}
