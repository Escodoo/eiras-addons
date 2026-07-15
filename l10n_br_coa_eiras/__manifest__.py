# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Plano de Contas - Eiras",
    "version": "16.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/eiras-addons",
    "depends": ["l10n_br_coa"],
    "data": [
        "data/account_chart_template.xml",
        "data/account_group.xml",
        "data/account.account.template.csv",
        "data/account_fiscal_position_template.xml",
        "data/account_chart_template_post.xml",
    ],
    "post_init_hook": "post_init_hook",
}
