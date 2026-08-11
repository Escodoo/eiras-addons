# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Eiras L10n BR NFSe Obra Custom",
    "summary": """
        Adds construction site (Obra) data to invoices and sends it in the
        Focus NFe NFSe Municipal payload""",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/eiras-addons",
    "depends": [
        "l10n_br_account",
        "l10n_br_purchase",
        "l10n_br_nfse_focus",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/l10n_br_fiscal_obra_views.xml",
        "views/account_move_views.xml",
    ],
}
