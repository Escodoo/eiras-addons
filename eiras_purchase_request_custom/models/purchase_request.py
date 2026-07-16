# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Cost Center",
        compute="_compute_analytic_account_id",
        store=True,
    )

    @api.depends("line_ids.analytic_distribution")
    def _compute_analytic_account_id(self):
        for request in self:
            line = request.line_ids[:1]
            distribution = line.analytic_distribution or {}
            account_ids = (
                list(distribution.keys()) if isinstance(distribution, dict) else []
            )
            request.analytic_account_id = int(account_ids[0]) if account_ids else False
