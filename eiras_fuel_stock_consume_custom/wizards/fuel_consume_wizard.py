# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class FuelConsumeWizard(models.TransientModel):
    _inherit = "fuel.consume.wizard"

    initial_register_value = fields.Float()
    final_register_value = fields.Float()

    def action_next(self):
        self.ensure_one()
        if self.initial_register_value or self.final_register_value:
            if self.final_register_value <= self.initial_register_value:
                raise ValidationError(
                    _(
                        "The final register value must be greater than the "
                        "initial register value."
                    )
                )
        return super(
            FuelConsumeWizard,
            self.with_context(
                default_initial_register_value=self.initial_register_value,
                default_final_register_value=self.final_register_value,
            ),
        ).action_next()
