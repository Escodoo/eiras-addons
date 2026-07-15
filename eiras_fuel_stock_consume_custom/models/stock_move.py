# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    initial_register_value = fields.Float(
        related="picking_id.initial_register_value",
        store=True,
        readonly=True,
    )
    final_register_value = fields.Float(
        related="picking_id.final_register_value",
        store=True,
        readonly=True,
    )
