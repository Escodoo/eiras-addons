# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FuelConsumeConfirmWizard(models.TransientModel):
    _inherit = "fuel.consume.confirm.wizard"

    initial_register_value = fields.Float(readonly=True)
    final_register_value = fields.Float(readonly=True)

    def action_confirm(self):
        return super(
            FuelConsumeConfirmWizard,
            self.with_context(
                default_initial_register_value=self.initial_register_value,
                default_final_register_value=self.final_register_value,
            ),
        ).action_confirm()
