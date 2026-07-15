# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Eiras Fuel Stock Consume Custom",
    "summary": """
        Eiras customization for Fuel Stock Consume: adds initial and final
        register values to the fuel consumption""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/eiras-addons",
    "depends": ["fuel_stock_consume"],
    "data": [
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/fuel_consume_wizard_views.xml",
    ],
    "installable": True,
}
