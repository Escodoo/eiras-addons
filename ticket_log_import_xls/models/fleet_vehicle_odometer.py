# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FleetVehicleOdometer(models.Model):
    _inherit = "fleet.vehicle.odometer"

    refueling_cost = fields.Integer()
