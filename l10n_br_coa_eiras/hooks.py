# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    coa_generic_tmpl = env.ref("l10n_br_coa_eiras.account_template_eiras")
    if env["ir.module.module"].search_count(
        [
            ("name", "=", "l10n_br_account"),
            ("state", "=", "installed"),
        ]
    ):
        # Relate fiscal taxes to account taxes.
        eiras_coa_charts = env["account.chart.template"].search(
            [("parent_id", "=", env.ref("l10n_br_coa_eiras.account_template_eiras").id)]
        )
        for eiras_coa_chart in eiras_coa_charts:
            eiras_coa_chart.load_fiscal_taxes(env, coa_generic_tmpl)
