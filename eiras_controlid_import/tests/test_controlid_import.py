# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime

import pytz

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon

from ..wizards.controlid_import_wizard import _parse_time

_H = (
    "C0;C1;C2;Nome;C4;C5;C6;C7;C8;C9;C10;C11;C12;Dia;Prev;"
    "E1;X1;E2;X2;C19;C20;C21;C22;C23;C24;C25;C26;C27;Just"
)


def _row(name, date, e1="", x1="", e2="", x2="", notes=""):
    return (
        f"C;C;C;{name};C;C;C;C;C;C;C;C;C;{date}; ;"
        f"{e1};{x1};{e2};{x2}; ; ; ; ; ; ; ; ; ;{notes}"
    )


def _csv(*rows):
    return base64.b64encode("\n".join([_H] + list(rows)).encode()).decode()


@tagged("post_install", "-at_install")
class TestParseTime(BaseCommon):
    def test_valid_formats(self):
        self.assertEqual(_parse_time("07:46"), "07:46")
        self.assertEqual(_parse_time("07:30 (I)"), "07:30")
        self.assertEqual(_parse_time("12:00 (P)"), "12:00")

    def test_none_cases(self):
        for v in ("", None, "   ", "Folga", "folga", "abc"):
            self.assertIsNone(_parse_time(v), msg=f"expected None for {v!r}")


@tagged("post_install", "-at_install")
class TestControlidImportWizard(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = "America/Sao_Paulo"
        cls.project = cls.env["project.project"].create(
            {"name": "Test Project", "allow_timesheets": True}
        )
        cls.employee = cls.env["hr.employee"].create({"name": "JOAO DA SILVA TESTE"})

    def _wizard(self, csv_b64, skip=True):
        return self.env["eiras.controlid.import"].create(
            {
                "csv_file": csv_b64,
                "csv_filename": "test.csv",
                "default_project_id": self.project.id,
                "default_description": "Test",
                "skip_existing": skip,
            }
        )

    def _utc(self, date_str, time_str):
        tz = pytz.timezone("America/Sao_Paulo")
        return (
            tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
            .astimezone(pytz.utc)
            .replace(tzinfo=None)
        )

    def test_analyze(self):
        csv_b64 = _csv(
            _row("JOAO DA SILVA TESTE", "01/03/2026 DOM", "Folga", "Folga"),
            _row(
                "JOAO DA SILVA TESTE",
                "02/03/2026 SEG",
                "07:46",
                "12:00 (P)",
                "13:00 (P)",
                "18:08",
            ),
            _row("joao da silva teste", "03/03/2026 TER", "08:00 (I)", "17:00 (I)"),
            _row("NAO EXISTE", "02/03/2026 SEG", "08:00", "17:00"),
        )
        wiz = self._wizard(csv_b64)
        wiz.action_analyze()
        self.assertEqual(wiz.state, "preview")
        self.assertEqual(wiz.total_lines, 3)
        self.assertEqual(wiz.found_lines, 2)
        self.assertEqual(wiz.not_found_lines, 1)
        dates = sorted(str(line.date) for line in wiz.line_ids.filtered("employee_id"))
        self.assertEqual(dates, ["2026-03-02", "2026-03-03"])

    def test_analyze_empty_raises(self):
        with self.assertRaises(UserError):
            self._wizard(_csv()).action_analyze()

    def test_analyze_notes(self):
        csv_b64 = _csv(
            _row(
                "JOAO DA SILVA TESTE",
                "17/03/2026 TER",
                "08:00",
                "15:00",
                notes="Atestado",
            )
        )
        wiz = self._wizard(csv_b64)
        wiz.action_analyze()
        self.assertEqual(wiz.line_ids.notes, "Atestado")

    def test_import_creates_timesheets(self):
        csv_b64 = _csv(
            _row(
                "JOAO DA SILVA TESTE",
                "02/03/2026 SEG",
                "08:00",
                "12:00",
                "13:00",
                "17:00",
            )
        )
        wiz = self._wizard(csv_b64, skip=False)
        wiz.action_analyze()
        result = wiz.action_import()
        lines = self.env["account.analytic.line"].browse(result["domain"][0][2])
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].employee_id, self.employee)
        self.assertEqual(lines[0].project_id, self.project)
        self.assertEqual(lines[0].date_time, self._utc("2026-03-02", "08:00"))
        self.assertEqual(lines[1].date_time_end, self._utc("2026-03-02", "17:00"))

    def test_import_notes_as_description(self):
        csv_b64 = _csv(
            _row(
                "JOAO DA SILVA TESTE",
                "04/03/2026 QUA",
                "09:00",
                "18:00",
                notes="Viagem",
            )
        )
        wiz = self._wizard(csv_b64, skip=False)
        wiz.action_analyze()
        result = wiz.action_import()
        line = self.env["account.analytic.line"].browse(result["domain"][0][2])
        self.assertEqual(line.name, "Viagem")

    def test_import_skip_existing(self):
        csv_b64 = _csv(_row("JOAO DA SILVA TESTE", "05/03/2026 QUI", "10:00", "14:00"))
        w1 = self._wizard(csv_b64, skip=False)
        w1.action_analyze()
        w1.action_import()
        w2 = self._wizard(csv_b64, skip=True)
        w2.action_analyze()
        with self.assertRaises(UserError):
            w2.action_import()

    def test_import_no_valid_lines_raises(self):
        csv_b64 = _csv(_row("JOAO DA SILVA TESTE", "06/03/2026 SEX", "08:00", "12:00"))
        wiz = self._wizard(csv_b64, skip=False)
        wiz.action_analyze()
        wiz.line_ids.write({"skip": True})
        with self.assertRaises(UserError):
            wiz.action_import()

    def test_import_no_employee_raises(self):
        csv_b64 = _csv(_row("NAO EXISTE", "06/03/2026 SEX", "08:00", "12:00"))
        wiz = self._wizard(csv_b64, skip=False)
        wiz.action_analyze()
        with self.assertRaises(UserError):
            wiz.action_import()
