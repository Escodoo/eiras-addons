# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class FuelConsumeWizard(models.TransientModel):
    _name = "fuel.consume.wizard"
    _description = "Fuel Consumption Wizard"

    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Supply Location",
        required=True,
        domain="[('replenish_location', '=', True)]",
    )
    available_qty = fields.Float(
        string="Available Quantity",
        compute="_compute_available_qty",
        readonly=True,
    )
    consume_qty = fields.Float(
        string="Quantity to Consume",
        required=True,
    )
    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        string="Vehicle",
        required=True,
    )
    driver_id = fields.Many2one(
        comodel_name="res.partner",
        string="Driver",
        required=True,
    )
    odometer = fields.Float(
        required=True,
    )

    @api.depends("location_id")
    def _compute_available_qty(self):
        for rec in self:
            if not rec.location_id:
                rec.available_qty = 0.0
                continue
            pickings = self.env["stock.picking"].search(
                [
                    ("state", "=", "assigned"),
                    ("location_id", "=", rec.location_id.id),
                ]
            )
            total = 0.0
            for picking in pickings:
                for move in picking.move_ids:
                    total += move.reserved_availability
            rec.available_qty = total

    def _get_available_pickings(self):
        self.ensure_one()
        return self.env["stock.picking"].search(
            [
                ("state", "=", "assigned"),
                ("location_id", "=", self.location_id.id),
            ],
            order="scheduled_date asc",
        )

    def _consume_move(self, move, qty):
        """Set qty_done on move lines to consume the given quantity."""
        remaining = qty
        precision = move.product_uom.rounding
        for line in move.move_line_ids:
            if remaining <= 0:
                break
            if float_compare(line.reserved_qty, 0.0, precision_rounding=precision) <= 0:
                continue
            consume = min(remaining, line.reserved_qty)
            line.qty_done = consume
            remaining -= consume
        return qty - remaining

    def _consume_picking(self, picking, qty):
        """Partially consume a picking and validate it, creating backorder automatically."""
        self.ensure_one()
        remaining = qty
        for move in picking.move_ids.filtered(lambda m: m.state == "assigned"):
            if remaining <= 0:
                break
            if (
                float_compare(
                    move.reserved_availability,
                    0.0,
                    precision_rounding=move.product_uom.rounding,
                )
                <= 0
            ):
                continue
            consumed = self._consume_move(
                move, min(remaining, move.reserved_availability)
            )
            remaining -= consumed

        consumed_qty = qty - remaining
        if float_compare(consumed_qty, 0.0, precision_rounding=0.001) > 0:
            picking.write(
                {
                    "vehicle_id": self.vehicle_id.id,
                    "driver_id": self.driver_id.id,
                    "odometer_value": self.odometer,
                }
            )
            picking._action_done()
        return consumed_qty

    def _create_odometer(self):
        self.ensure_one()
        self.env["fleet.vehicle.odometer"].create(
            {
                "vehicle_id": self.vehicle_id.id,
                "value": self.odometer,
                "date": fields.Datetime.now(),
                "driver_id": self.driver_id.id,
            }
        )

    def action_confirm_consumption(self):
        self.ensure_one()
        if not self.location_id:
            raise UserError(_("Supply location is required."))
        if float_compare(self.consume_qty, 0.0, precision_rounding=0.001) <= 0:
            raise UserError(_("Quantity must be greater than zero."))
        if (
            float_compare(
                self.consume_qty, self.available_qty, precision_rounding=0.001
            )
            > 0
        ):
            raise UserError(
                _(
                    "Quantity (%(consume)s) exceeds available quantity (%(available)s).",
                    consume=self.consume_qty,
                    available=self.available_qty,
                )
            )
        if not self.vehicle_id:
            raise UserError(_("Vehicle is required."))
        if not self.driver_id:
            raise UserError(_("Driver is required."))
        if float_compare(self.odometer, 0.0, precision_rounding=0.001) <= 0:
            raise UserError(_("Odometer value must be greater than zero."))

        pickings = self._get_available_pickings()
        if not pickings:
            raise UserError(_("No available pickings for the selected location."))

        remaining = self.consume_qty
        processed = self.env["stock.picking"]
        for picking in pickings:
            if float_compare(remaining, 0.0, precision_rounding=0.001) <= 0:
                break
            consumed = self._consume_picking(picking, remaining)
            if float_compare(consumed, 0.0, precision_rounding=0.001) > 0:
                remaining -= consumed
                processed |= picking

        if not processed:
            raise UserError(
                _("Could not process consumption. No pickings in assigned state.")
            )

        self._create_odometer()

        return {
            "type": "ir.actions.act_window",
            "name": _("Fuel Consumption - Processed Pickings"),
            "res_model": "stock.picking",
            "view_mode": "tree,form",
            "domain": [("id", "in", processed.ids)],
            "context": {},
        }
