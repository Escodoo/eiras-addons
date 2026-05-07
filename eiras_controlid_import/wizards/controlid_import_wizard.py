# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import csv
import io
import re
from datetime import datetime

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_COL_EMPLOYEE_NAME = 3
_COL_DATE = 13
_COL_ENTRY1 = 15
_COL_EXIT1 = 16
_COL_ENTRY2 = 17
_COL_EXIT2 = 18
_COL_NOTES = 28


def _parse_time(value):
    """Extract HH:MM from '07:46', '07:46 (I)', '07:46 (P)', or return None."""
    if not value:
        return None
    value = value.strip()
    if not value or value.lower() == "folga":
        return None
    m = re.match(r"(\d{2}:\d{2})", value)
    return m.group(1) if m else None


class ControlidImportWizard(models.TransientModel):
    _name = "eiras.controlid.import"
    _description = "Import Control ID Attendance"

    csv_file = fields.Binary(string="CSV File", required=True)
    csv_filename = fields.Char()
    state = fields.Selection(
        selection=[("draft", "Select"), ("preview", "Preview")],
        default="draft",
        required=True,
    )
    default_project_id = fields.Many2one(
        comodel_name="project.project",
        string="Default Project",
        domain=[("allow_timesheets", "=", True)],
        required=True,
    )
    default_description = fields.Char(
        default="Control ID Import",
    )
    skip_existing = fields.Boolean(
        string="Skip Existing Records",
        default=True,
    )
    line_ids = fields.One2many(
        comodel_name="eiras.controlid.import.line",
        inverse_name="wizard_id",
        string="Lines",
    )
    total_lines = fields.Integer(compute="_compute_totals")
    found_lines = fields.Integer(compute="_compute_totals", string="Employees Found")
    not_found_lines = fields.Integer(compute="_compute_totals", string="Not Found")

    @api.depends("line_ids", "line_ids.employee_id")
    def _compute_totals(self):
        for rec in self:
            rec.total_lines = len(rec.line_ids)
            rec.found_lines = len(rec.line_ids.filtered(lambda l: l.employee_id))
            rec.not_found_lines = len(
                rec.line_ids.filtered(lambda l: not l.employee_id)
            )

    def _decode_csv(self):
        data = base64.b64decode(self.csv_file)
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return data.decode("latin-1")

    def _parse_rows(self):
        text = self._decode_csv()
        reader = csv.reader(io.StringIO(text), delimiter=";")
        rows = list(reader)
        return rows[1:] if len(rows) > 1 else []

    def action_analyze(self):
        self.ensure_one()
        rows = self._parse_rows()
        self.line_ids.unlink()

        employee_cache = {}
        vals_list = []

        for row in rows:
            if len(row) <= _COL_DATE:
                continue

            date_raw = row[_COL_DATE].strip()
            if not date_raw or len(date_raw) < 10:
                continue

            try:
                date = datetime.strptime(date_raw[:10], "%d/%m/%Y").date()
            except ValueError:
                continue

            def _get(idx):
                return row[idx].strip() if len(row) > idx else ""

            entry1 = _parse_time(_get(_COL_ENTRY1))
            exit1 = _parse_time(_get(_COL_EXIT1))
            entry2 = _parse_time(_get(_COL_ENTRY2))
            exit2 = _parse_time(_get(_COL_EXIT2))

            if not entry1 and not entry2:
                continue

            employee_name = _get(_COL_EMPLOYEE_NAME)
            notes = _get(_COL_NOTES)

            if employee_name not in employee_cache:
                emp = self.env["hr.employee"].search(
                    [("name", "=ilike", employee_name)], limit=1
                )
                employee_cache[employee_name] = emp.id if emp else False

            vals_list.append(
                {
                    "wizard_id": self.id,
                    "employee_name": employee_name,
                    "employee_id": employee_cache[employee_name],
                    "date": date,
                    "entry1": entry1 or "",
                    "exit1": exit1 or "",
                    "entry2": entry2 or "",
                    "exit2": exit2 or "",
                    "notes": notes,
                }
            )

        if not vals_list:
            raise UserError(
                _("No attendance records found in the file. Please check the format.")
            )

        self.env["eiras.controlid.import.line"].create(vals_list)
        self.state = "preview"

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def _get_tz(self):
        return pytz.timezone(
            self.env.user.tz or self.env.company.partner_id.tz or "America/Sao_Paulo"
        )

    def _to_utc(self, date, time_str):
        tz = self._get_tz()
        dt_local = tz.localize(
            datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
        )
        return dt_local.astimezone(pytz.utc).replace(tzinfo=None)

    def action_import(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.employee_id and not l.skip)
        if not lines:
            raise UserError(
                _(
                    "No lines available for import. "
                    "Make sure employees were found and are not marked as 'Skip'."
                )
            )

        Timesheet = self.env["account.analytic.line"]
        created_ids = []

        for line in lines:
            description = line.notes or self.default_description
            for entry, exit_ in ((line.entry1, line.exit1), (line.entry2, line.exit2)):
                if not entry or not exit_:
                    continue
                date_time_start = self._to_utc(line.date, entry)
                date_time_end = self._to_utc(line.date, exit_)
                if self.skip_existing and Timesheet.search(
                    [
                        ("employee_id", "=", line.employee_id.id),
                        ("date_time", "=", date_time_start),
                    ],
                    limit=1,
                ):
                    continue
                rec = Timesheet.create(
                    {
                        "employee_id": line.employee_id.id,
                        "project_id": self.default_project_id.id,
                        "date": line.date,
                        "date_time": date_time_start,
                        "date_time_end": date_time_end,
                        "name": description,
                    }
                )
                created_ids.append(rec.id)

        if not created_ids:
            raise UserError(
                _(
                    "All records already exist in the system. "
                    "Uncheck 'Skip Existing Records' to reimport."
                )
            )

        return {
            "name": _("Imported Timesheet Lines"),
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "view_mode": "list,form",
            "domain": [("id", "in", created_ids)],
            "target": "current",
        }


class ControlidImportLine(models.TransientModel):
    _name = "eiras.controlid.import.line"
    _description = "Control ID Import Line"
    _order = "employee_name, date"

    wizard_id = fields.Many2one(
        comodel_name="eiras.controlid.import",
        required=True,
        ondelete="cascade",
    )
    employee_name = fields.Char(string="Employee (CSV)", readonly=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Odoo Employee")
    date = fields.Date(readonly=True)
    entry1 = fields.Char(string="Check In 1", readonly=True)
    exit1 = fields.Char(string="Check Out 1", readonly=True)
    entry2 = fields.Char(string="Check In 2", readonly=True)
    exit2 = fields.Char(string="Check Out 2", readonly=True)
    notes = fields.Char(readonly=True)
    skip = fields.Boolean()
