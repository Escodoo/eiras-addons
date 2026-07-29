{
    "name": "Ticket Log Import XLS",
    "version": "16.0.1.0.0",
    "category": "Purchase",
    "summary": "Import ticket log data from XLS/XLSX files (fuel and toll)",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/eiras-addons",
    "license": "AGPL-3",
    "depends": ["fleet_vehicle_purchase"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/ticket_log_wizard_view.xml",
        "views/ticket_log_import_line_view.xml",
        "views/fleet_vehicle_views.xml",
    ],
    "application": False,
    "auto_install": False,
}
