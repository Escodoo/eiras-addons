# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FuelConsumeWizard(models.TransientModel):
    _inherit = "fuel.consume.wizard"

    initial_register_value = fields.Float()
    final_register_value = fields.Float()

    @api.onchange("picking_type_id")
    def _onchange_picking_type_id(self):
        """Fill the source location with the operation type default one."""
        if self.picking_type_id.default_location_src_id:
            self.location_id = self.picking_type_id.default_location_src_id

    @api.onchange("initial_register_value", "final_register_value")
    def _onchange_register_values(self):
        """Compute the quantity from the pump register readings.

        When both readings are filled, the consumed quantity is their
        difference, expressed in the unit of measure of the chosen product.
        The quantity field is set read-only in that case (see the form view).
        """
        if self.initial_register_value and self.final_register_value:
            if self.final_register_value < self.initial_register_value:
                self.product_uom_qty = (
                    self.initial_register_value - self.final_register_value
                )

    def action_next(self):
        self.ensure_one()
        if self.initial_register_value or self.final_register_value:
            if self.final_register_value >= self.initial_register_value:
                raise ValidationError(
                    _(
                        "The final register value must be lower than the "
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
