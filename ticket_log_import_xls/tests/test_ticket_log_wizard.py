import base64
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestTicketLogWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fleet_model = cls.env["fleet.vehicle.model"].search([], limit=1)
        cls.analytic_plan = cls.env["account.analytic.plan"].search([], limit=1)
        cls.vehicle_1 = cls.env["fleet.vehicle"].create(
            {
                "name": "FFZ7999",
                "license_plate": "FFZ7999",
                "model_id": cls.fleet_model.id,
            }
        )
        cls.vehicle_2 = cls.env["fleet.vehicle"].create(
            {
                "name": "GTN2J67",
                "license_plate": "GTN2J67",
                "model_id": cls.fleet_model.id,
            }
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "ROTA",
                "plan_id": cls.analytic_plan.id,
            }
        )
        cls.driver_1 = cls.env["res.partner"].create(
            {
                "name": "TARCISIO ALVES DE MELO",
            }
        )
        cls.driver_2 = cls.env["res.partner"].create(
            {
                "name": "JOAO SILVA",
            }
        )
        cls.product_gasoline = cls.env["product.product"].create(
            {
                "name": "GASOLINA COMUM",
                "type": "service",
            }
        )
        cls.product_diesel = cls.env["product.product"].create(
            {
                "name": "DIESEL",
                "type": "service",
            }
        )
        cls.product_ethanol = cls.env["product.product"].create(
            {
                "name": "ETANOL",
                "type": "service",
            }
        )
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Test Vendor",
                "supplier_rank": 1,
            }
        )

    def _create_mock_sheet(self, rows):
        mock_sheet = MagicMock()
        mock_sheet.nrows = len(rows) + 1
        mock_sheet.cell_value = (
            lambda row, col: rows[row - 1][col]
            if row <= len(rows) and col < len(rows[row - 1])
            else ""
        )
        return mock_sheet

    def _create_mock_workbook(self, rows):
        mock_workbook = MagicMock()
        mock_workbook.sheet_by_index = lambda idx: self._create_mock_sheet(rows)
        return mock_workbook

    def test_convert_float_float(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        result = wizard._convert_float(10.5)
        self.assertEqual(result, 10.5)

    def test_convert_float_string_with_currency(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        result = wizard._convert_float("R$ 10,50")
        self.assertEqual(result, 10.50)

    def test_convert_float_string_invalid(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        result = wizard._convert_float("invalid")
        self.assertEqual(result, 0.0)

    def test_parse_date_string_br(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        result = wizard._parse_date("01/02/2026")
        self.assertEqual(str(result), "2026-02-01")

    def test_parse_date_string_iso(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        result = wizard._parse_date("2026-02-01")
        self.assertEqual(str(result), "2026-02-01")

    def test_parse_date_float_excel(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )

        result = wizard._parse_date(45350.0)
        self.assertIsInstance(result, type(fields.Date.today()))

    def test_normalize_plate(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        result = wizard._normalize_plate("ffz7999 ")
        self.assertEqual(result, "FFZ7999")

    def test_compute_hash_consistent(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        data = {
            "date": "2026-02-01",
            "license_plate": "FFZ7999",
            "driver_name": "TARCISIO ALVES DE MELO",
            "fuel_type": "GASOLINA COMUM",
            "liters": 27.89,
            "price_per_liter": 5.891,
            "odometer": 336492,
        }
        hash1 = wizard._compute_hash(data)
        hash2 = wizard._compute_hash(data)
        self.assertEqual(hash1, hash2)

    def test_compute_hash_different(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        data1 = {"date": "2026-02-01", "license_plate": "FFZ7999", "liters": 10}
        data2 = {"date": "2026-02-02", "license_plate": "FFZ7999", "liters": 10}
        hash1 = wizard._compute_hash(data1)
        hash2 = wizard._compute_hash(data2)
        self.assertNotEqual(hash1, hash2)

    def test_find_vehicle_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        vehicle = wizard._find_vehicle("FFZ7999")
        self.assertTrue(vehicle)
        self.assertEqual(vehicle.license_plate, "FFZ7999")

    def test_find_vehicle_not_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        vehicle = wizard._find_vehicle("XXX9999")
        self.assertFalse(vehicle)

    def test_find_analytic_account_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        account = wizard._find_analytic_account("ROTA")
        self.assertTrue(account)
        self.assertEqual(account.name, "ROTA")

    def test_find_analytic_account_not_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        account = wizard._find_analytic_account("OBRA_INEXISTENTE")
        self.assertFalse(account)

    def test_find_driver_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        driver = wizard._find_driver("TARCISIO ALVES DE MELO")
        self.assertTrue(driver)
        self.assertEqual(driver.name, "TARCISIO ALVES DE MELO")

    def test_find_driver_not_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        driver = wizard._find_driver("MOTORISTA_INEXISTENTE")
        self.assertFalse(driver)

    def test_find_product_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        product = wizard._find_product("GASOLINA COMUM")
        self.assertTrue(product)
        self.assertEqual(product.name, "GASOLINA COMUM")

    def test_find_product_not_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        product = wizard._find_product("PRODUTO_INEXISTENTE")
        self.assertFalse(product)

    def test_action_preview_no_file(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_preview()

    def test_action_preview_valid_data(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        rows = [
            [
                "2026-02-01 06:05:42",
                "FFZ7999",
                "VL05",
                "ROTA",
                "TARCISIO ALVES DE MELO",
                "GASOLINA COMUM",
                27.89,
                5.891,
                336492,
                261,
                9.36,
                164.3,
            ],
            [
                "2026-02-01 07:00:00",
                "GTN2J67",
                "VL66",
                "ROTA",
                "JOAO SILVA",
                "DIESEL",
                50.0,
                6.0,
                100000,
                300,
                6.0,
                300.0,
            ],
        ]
        with patch("xlrd.open_workbook", return_value=self._create_mock_workbook(rows)):
            with patch("base64.b64decode", return_value=b""):
                wizard.file = base64.b64encode(b"test")
                wizard.action_preview()
        self.assertEqual(wizard.state, "preview")
        self.assertEqual(len(wizard.preview_line_ids), 2)
        valid_lines = wizard.preview_line_ids.filtered(lambda line: line.is_valid)
        self.assertEqual(len(valid_lines), 2)

    def test_action_preview_vehicle_not_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        rows = [
            [
                "2026-02-01 06:05:42",
                "XXX9999",
                "VL05",
                "ROTA",
                "TARCISIO ALVES DE MELO",
                "GASOLINA COMUM",
                27.89,
                5.891,
                336492,
                261,
                9.36,
                164.3,
            ],
        ]
        with patch("xlrd.open_workbook", return_value=self._create_mock_workbook(rows)):
            with patch("base64.b64decode", return_value=b""):
                wizard.file = base64.b64encode(b"test")
                wizard.action_preview()
        self.assertEqual(wizard.state, "preview")
        invalid_line = wizard.preview_line_ids.filtered(lambda line: not line.is_valid)
        self.assertEqual(len(invalid_line), 1)
        self.assertIn("not found", invalid_line.error_message)

    def test_action_preview_analytic_not_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        rows = [
            [
                "2026-02-01 06:05:42",
                "FFZ7999",
                "VL05",
                "OBRA_INEXISTENTE",
                "TARCISIO ALVES DE MELO",
                "GASOLINA COMUM",
                27.89,
                5.891,
                336492,
                261,
                9.36,
                164.3,
            ],
        ]
        with patch("xlrd.open_workbook", return_value=self._create_mock_workbook(rows)):
            with patch("base64.b64decode", return_value=b""):
                wizard.file = base64.b64encode(b"test")
                wizard.action_preview()
        self.assertEqual(wizard.state, "preview")
        invalid_line = wizard.preview_line_ids.filtered(lambda line: not line.is_valid)
        self.assertEqual(len(invalid_line), 1)
        self.assertIn("Analytic account", invalid_line.error_message)

    def test_action_preview_driver_not_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        rows = [
            [
                "2026-02-01 06:05:42",
                "FFZ7999",
                "VL05",
                "ROTA",
                "MOTORISTA_INEXISTENTE",
                "GASOLINA COMUM",
                27.89,
                5.891,
                336492,
                261,
                9.36,
                164.3,
            ],
        ]
        with patch("xlrd.open_workbook", return_value=self._create_mock_workbook(rows)):
            with patch("base64.b64decode", return_value=b""):
                wizard.file = base64.b64encode(b"test")
                wizard.action_preview()
        self.assertEqual(wizard.state, "preview")
        invalid_line = wizard.preview_line_ids.filtered(lambda line: not line.is_valid)
        self.assertEqual(len(invalid_line), 1)
        self.assertIn("Driver", invalid_line.error_message)

    def test_action_preview_product_not_found(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        rows = [
            [
                "2026-02-01 06:05:42",
                "FFZ7999",
                "VL05",
                "ROTA",
                "TARCISIO ALVES DE MELO",
                "PRODUTO_INEXISTENTE",
                27.89,
                5.891,
                336492,
                261,
                9.36,
                164.3,
            ],
        ]
        with patch("xlrd.open_workbook", return_value=self._create_mock_workbook(rows)):
            with patch("base64.b64decode", return_value=b""):
                wizard.file = base64.b64encode(b"test")
                wizard.action_preview()
        self.assertEqual(wizard.state, "preview")
        invalid_line = wizard.preview_line_ids.filtered(lambda line: not line.is_valid)
        self.assertEqual(len(invalid_line), 1)
        self.assertIn("Product", invalid_line.error_message)

    def test_action_import_no_preview_lines(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_import()

    def test_action_import_invalid_lines(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        line = self.env["ticket.log.wizard.line"].create(
            {
                "wizard_id": wizard.id,
                "license_plate": "XXX9999",
                "is_valid": False,
                "error_message": "Vehicle not found",
            }
        )
        wizard.preview_line_ids = line
        with self.assertRaises(UserError):
            wizard.action_import()

    def test_action_import_creates_po(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        line = self.env["ticket.log.wizard.line"].create(
            {
                "wizard_id": wizard.id,
                "date": "2026-02-01",
                "license_plate": "FFZ7999",
                "work": "ROTA",
                "driver_name": "TARCISIO ALVES DE MELO",
                "fuel_type": "GASOLINA COMUM",
                "liters": 27.89,
                "price_per_liter": 5.891,
                "odometer": 336492,
                "total_value": 164.3,
                "vehicle_id": self.vehicle_1.id,
                "driver_id": self.driver_1.id,
                "product_id": self.product_gasoline.id,
                "analytic_account_id": self.analytic_account.id,
                "is_valid": True,
            }
        )
        wizard.preview_line_ids = line
        wizard.state = "preview"
        wizard.action_import()
        self.assertEqual(wizard.state, "done")
        po = self.env["purchase.order"].search([("partner_id", "=", self.vendor.id)])
        self.assertTrue(po)
        self.assertEqual(len(po.order_line), 1)
        self.assertEqual(po.order_line.product_id.name, "GASOLINA COMUM")

    def test_action_import_creates_odometer(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        line = self.env["ticket.log.wizard.line"].create(
            {
                "wizard_id": wizard.id,
                "date": "2026-02-01",
                "license_plate": "FFZ7999",
                "work": "ROTA",
                "driver_name": "TARCISIO ALVES DE MELO",
                "fuel_type": "GASOLINA COMUM",
                "liters": 27.89,
                "price_per_liter": 5.891,
                "odometer": 336500,
                "total_value": 164.3,
                "vehicle_id": self.vehicle_1.id,
                "driver_id": self.driver_1.id,
                "product_id": self.product_gasoline.id,
                "analytic_account_id": self.analytic_account.id,
                "is_valid": True,
            }
        )
        wizard.preview_line_ids = line
        wizard.state = "preview"
        wizard.action_import()
        odometer = self.env["fleet.vehicle.odometer"].search(
            [
                ("vehicle_id.license_plate", "=", "FFZ7999"),
                ("value", "=", 336500),
            ]
        )
        self.assertTrue(odometer)

    def test_action_import_updates_driver(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        self.vehicle_1.driver_id = False
        line = self.env["ticket.log.wizard.line"].create(
            {
                "wizard_id": wizard.id,
                "date": "2026-02-01",
                "license_plate": "FFZ7999",
                "work": "ROTA",
                "driver_name": "TARCISIO ALVES DE MELO",
                "fuel_type": "GASOLINA COMUM",
                "liters": 27.89,
                "price_per_liter": 5.891,
                "odometer": 0,
                "total_value": 164.3,
                "vehicle_id": self.vehicle_1.id,
                "driver_id": self.driver_1.id,
                "product_id": self.product_gasoline.id,
                "analytic_account_id": self.analytic_account.id,
                "is_valid": True,
            }
        )
        wizard.preview_line_ids = line
        wizard.state = "preview"
        wizard.action_import()
        vehicle = self.env["fleet.vehicle"].search([("license_plate", "=", "FFZ7999")])
        self.assertIn("TARCISIO ALVES DE MELO", vehicle.driver_id.mapped("name"))

    def test_action_import_duplicate_detection(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
            }
        )
        line = self.env["ticket.log.wizard.line"].create(
            {
                "wizard_id": wizard.id,
                "date": "2026-02-01",
                "license_plate": "FFZ7999",
                "work": "ROTA",
                "driver_name": "TARCISIO ALVES DE MELO",
                "fuel_type": "GASOLINA COMUM",
                "liters": 27.89,
                "price_per_liter": 5.891,
                "odometer": 0,
                "total_value": 164.3,
                "vehicle_id": self.vehicle_1.id,
                "driver_id": self.driver_1.id,
                "product_id": self.product_gasoline.id,
                "analytic_account_id": self.analytic_account.id,
                "is_valid": True,
            }
        )
        wizard.preview_line_ids = line
        wizard.state = "preview"
        wizard.action_import()
        line_count_1 = self.env["ticket.log.import.line"].search_count([])
        wizard.action_reset()
        wizard.state = "draft"
        line2 = self.env["ticket.log.wizard.line"].create(
            {
                "wizard_id": wizard.id,
                "date": "2026-02-01",
                "license_plate": "FFZ7999",
                "work": "ROTA",
                "driver_name": "TARCISIO ALVES DE MELO",
                "fuel_type": "GASOLINA COMUM",
                "liters": 27.89,
                "price_per_liter": 5.891,
                "odometer": 0,
                "total_value": 164.3,
                "vehicle_id": self.vehicle_1.id,
                "driver_id": self.driver_1.id,
                "product_id": self.product_gasoline.id,
                "analytic_account_id": self.analytic_account.id,
                "is_valid": True,
            }
        )
        wizard.preview_line_ids = line2
        wizard.state = "preview"
        wizard.action_import()
        line_count_2 = self.env["ticket.log.import.line"].search_count([])
        self.assertEqual(line_count_1, line_count_2)

    def test_action_reset(self):
        wizard = self.env["ticket.log.wizard"].create(
            {
                "import_type": "fuel",
                "partner_id": self.vendor.id,
                "state": "preview",
                "error_summary": "test error",
            }
        )
        wizard.action_reset()
        self.assertEqual(wizard.state, "draft")
        self.assertFalse(wizard.error_summary)

    def test_default_get_fuel(self):
        wizard = (
            self.env["ticket.log.wizard"]
            .with_context(default_import_type="fuel")
            .create(
                {
                    "partner_id": self.vendor.id,
                }
            )
        )
        self.assertEqual(wizard.import_type, "fuel")

    def test_default_get_toll(self):
        wizard = (
            self.env["ticket.log.wizard"]
            .with_context(default_import_type="toll")
            .create(
                {
                    "partner_id": self.vendor.id,
                }
            )
        )
        self.assertEqual(wizard.import_type, "toll")
