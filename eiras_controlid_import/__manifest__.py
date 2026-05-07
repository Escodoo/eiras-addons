# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import Control ID Attendance",
    "version": "16.0.1.0.0",
    "category": "Human Resources/Attendance",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/eiras-addons",
    "summary": "Import attendance records from Control ID CSV export",
    "depends": ["hr_timesheet_calendar"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/controlid_import_wizard.xml",
        "views/hr_timesheet_menu.xml",
    ],
    "installable": True,
}
