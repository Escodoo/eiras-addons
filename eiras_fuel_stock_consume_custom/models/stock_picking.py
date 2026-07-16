# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    initial_register_value = fields.Float()
    final_register_value = fields.Float()

    @api.constrains("initial_register_value", "final_register_value")
    def _check_register_values(self):
        for picking in self:
            if picking.initial_register_value or picking.final_register_value:
                if picking.final_register_value <= picking.initial_register_value:
                    raise ValidationError(
                        _(
                            "The final register value must be greater than the "
                            "initial register value."
                        )
                    )
