# Copyright 2026 - Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Eiras Fuel Stock Consume Custom",
    "summary": """
        Fuel consumption wizard for truck refueling operations.
        Allows partial consumption of fuel from supply locations with
        automatic backorder generation and odometer recording.
    """,
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/eiras-addons",
    "depends": [
        "fuel_stock_consume",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/fuel_consume_wizard_view.xml",
    ],
}
