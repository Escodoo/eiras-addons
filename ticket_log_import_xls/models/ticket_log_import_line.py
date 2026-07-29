from odoo import fields, models


class TicketLogImportLine(models.Model):
    """Ticket Log Import Line.

    Stores imported ticket log records for duplicate control.
    Each record represents a line imported from XLS/XLSX file
    and is linked to a purchase order and its line.

    Fields include import type (fuel/toll), vehicle info,
    driver, product, quantities, prices, odometer, and
    a unique source hash to prevent duplicate imports.
    """

    _name = "ticket.log.import.line"
    _description = "Ticket Log Import Line"
    _order = "transaction_date desc, id desc"

    import_type = fields.Selection(
        [("fuel", "Fuel"), ("toll", "Toll")],
        required=True,
    )
    purchase_order_id = fields.Many2one("purchase.order")
    purchase_order_line_id = fields.Many2one("purchase.order.line")
    vehicle_id = fields.Many2one("fleet.vehicle")
    license_plate = fields.Char()
    transaction_date = fields.Date()
    driver_name = fields.Char()
    driver_id = fields.Many2one("res.partner")
    product_name = fields.Char()
    product_id = fields.Many2one("product.product")
    quantity = fields.Float()
    price_unit = fields.Float()
    total_value = fields.Float()
    odometer_value = fields.Float()
    analytic_account_id = fields.Many2one("account.analytic.account")
    source_hash = fields.Char(index=True)

    _sql_constraints = [
        ("source_hash_unique", "unique(source_hash)", "Duplicate import detected!")
    ]
