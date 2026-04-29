import base64
import hashlib
import logging
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.warning("xlrd not installed")


class TicketLogWizardLine(models.TransientModel):
    """Ticket Log Wizard Preview Line.

    Transient model to display imported data before creating
    purchase order lines. Shows validation status and errors
    for each row parsed from the XLS/XLSX file.
    """

    _name = "ticket.log.wizard.line"
    _description = "Ticket Log Wizard Preview Line"

    wizard_id = fields.Many2one(
        "ticket.log.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )

    row_number = fields.Integer()
    date = fields.Date()
    license_plate = fields.Char()
    fleet_number = fields.Char()
    work = fields.Char()
    driver_name = fields.Char()
    fuel_type = fields.Char()
    liters = fields.Float()
    price_per_liter = fields.Float()
    odometer = fields.Float()
    total_value = fields.Float()

    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle")
    driver_id = fields.Many2one("res.partner", string="Driver")
    product_id = fields.Many2one("product.product", string="Product")
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
    )

    error_message = fields.Char()
    is_valid = fields.Boolean(default=True)


class TicketLogWizard(models.TransientModel):
    """Ticket Log Import Wizard.

    Wizard for importing ticket log data from XLS/XLSX files.
    Supports fuel and toll imports.

    Workflow:
    1. User selects import type (fuel/toll), vendor, and XLS/XLSX file
    2. Preview action parses file and validates each row
    3. Import action creates purchase orders and related records

    Duplicate detection is performed using MD5 hash of
    date+plate+driver+product+qty+price+odometer.
    """

    _name = "ticket.log.wizard"
    _description = "Ticket Log Import Wizard"

    import_type = fields.Selection(
        [("fuel", "Fuel"), ("toll", "Toll")],
        required=True,
        default="fuel",
    )

    @api.model
    def default_get(self, fields):
        """Set default import_type from context.

        :param fields: Fields to include in default values
        :return: Dictionary of default values
        """
        res = super().default_get(fields)
        if self._context.get("default_import_type"):
            res["import_type"] = self._context.get("default_import_type")
        return res

    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        domain=[("supplier_rank", ">", 0)],
    )
    file = fields.Binary(string="XLS/XLSX File", required=True)
    filename = fields.Char()

    preview_line_ids = fields.One2many(
        "ticket.log.wizard.line",
        "wizard_id",
        string="Preview Lines",
    )

    state = fields.Selection(
        [("draft", "Draft"), ("preview", "Preview"), ("done", "Done")],
        default="draft",
    )

    order_count = fields.Integer(string="Orders Created", readonly=True)
    error_summary = fields.Text(string="Errors", readonly=True)

    def _parse_xlsx(self, file):
        """Decode base64 file and return first Excel sheet.

        :param file: Binary file data (base64 encoded)
        :return: xlrd sheet object (first sheet)
        """
        file_decoded = base64.b64decode(file)
        workbook = xlrd.open_workbook(file_contents=file_decoded)
        return workbook.sheet_by_index(0)

    def _convert_float(self, value):
        """Convert value to float, handling currency format.

        Handles Brazilian format (R$, comma as decimal separator).
        :param value: Input value (float or string)
        :return: Float value or 0.0 if conversion fails
        """
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            value = value.replace("R$", "").replace(",", ".").strip()
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    def _parse_date(self, value):
        """Convert value to date from string or Excel float.

        Supports formats: %d/%m/%Y %H:%M:%S, %d/%m/%Y, %Y-%m-%d
        :param value: Date as string or Excel float
        :return: date object
        """
        if isinstance(value, str):
            for fmt in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            return fields.Date.today()
        if isinstance(value, float):
            try:
                return datetime(*xlrd.xldate_as_tuple(value, 0)).date()
            except Exception:
                return fields.Date.today()
        return fields.Date.today()

    def _normalize_plate(self, plate):
        """Normalize license plate to uppercase without spaces.

        :param plate: License plate string
        :return: Normalized plate (uppercase, no spaces)
        """
        if not plate:
            return ""
        return str(plate).upper().strip().replace(" ", "")

    def _compute_hash(self, data_dict):
        """Generate MD5 hash for duplicate detection.

        Hash composed of: date|plate|driver|product|qty|price|odometer
        :param data_dict: Dictionary with import data
        :return: MD5 hash string (32 characters)
        """
        hash_string = (
            "{date}|{plate}|{driver}|{product}|{qty}|{price}|{odometer}".format(
                date=str(data_dict.get("date", "")),
                plate=data_dict.get("license_plate", ""),
                driver=data_dict.get("driver_name", ""),
                product=data_dict.get("fuel_type", ""),
                qty=str(data_dict.get("liters", 0)),
                price=str(data_dict.get("price_per_liter", 0)),
                odometer=str(data_dict.get("odometer", 0)),
            )
        )
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _find_vehicle(self, license_plate):
        """Search fleet.vehicle by normalized license_plate.

        :param license_plate: License plate to search
        :return: fleet.vehicle record or False
        """
        if not license_plate:
            return False
        normalized = self._normalize_plate(license_plate)
        return self.env["fleet.vehicle"].search(
            [
                ("license_plate", "=", normalized),
            ],
            limit=1,
        )

    def _find_analytic_account(self, work):
        """Search account.analytic.account by work name (ilike).

        :param work: Work/obra name from XLSX
        :return: account.analytic.account record or False
        """
        if not work:
            return False
        return self.env["account.analytic.account"].search(
            [
                ("name", "ilike", str(work).strip()),
            ],
            limit=1,
        )

    def _find_driver(self, driver_name):
        """Search res.partner (driver) by exact name.

        :param driver_name: Driver name from XLSX
        :return: res.partner record or False
        """
        if not driver_name:
            return False
        return self.env["res.partner"].search(
            [
                ("name", "=", str(driver_name).strip()),
            ],
            limit=1,
        )

    def _find_product(self, product_name):
        """Search product.product by name or default_code (ilike).

        :param product_name: Product/fuel type name
        :return: product.product record or False
        """
        if not product_name:
            return False
        return self.env["product.product"].search(
            [
                "|",
                ("name", "ilike", str(product_name).strip()),
                ("default_code", "ilike", str(product_name).strip()),
            ],
            limit=1,
        )

    def _check_duplicate(self, source_hash):
        """Check if source_hash already exists in import history.

        :param source_hash: MD5 hash to check
        :return: ticket.log.import.line record or False
        """
        return self.env["ticket.log.import.line"].search(
            [
                ("source_hash", "=", source_hash),
            ],
            limit=1,
        )

    def action_preview(self):
        """Parse XLSX file, validate each row, create preview lines.

        Validates: vehicle, analytic account, driver, product.
        Creates transient preview lines with validation status.
        Sets state to 'preview' on completion.
        :return: Wizard form reload action
        """
        self.ensure_one()
        if not self.file:
            raise UserError(_("Please select an XLS/XLSX file."))

        try:
            sheet = self._parse_xlsx(self.file)
        except Exception as e:
            raise UserError(_("Unable to read XLSX file: %s") % e) from e

        self.env.cr.execute(
            "DELETE FROM ticket_log_wizard_line WHERE wizard_id = %s", (self.id,)
        )

        row_count = sheet.nrows
        if row_count < 2:
            raise UserError(_("XLSX file must contain at least one data row."))

        preview_lines = self.env["ticket.log.wizard.line"]
        errors = []

        for row_idx in range(1, row_count):
            try:
                if self.import_type == "fuel":
                    date = sheet.cell_value(row_idx, 0)
                    license_plate = sheet.cell_value(row_idx, 1)
                    fleet_number = sheet.cell_value(row_idx, 2)
                    work = sheet.cell_value(row_idx, 3)
                    driver = sheet.cell_value(row_idx, 4)
                    fuel_type = sheet.cell_value(row_idx, 5)
                    liters = sheet.cell_value(row_idx, 6)
                    price_per_liter = sheet.cell_value(row_idx, 7)
                    odometer = sheet.cell_value(row_idx, 8)
                    total_value = sheet.cell_value(row_idx, 11)
                else:
                    date = sheet.cell_value(row_idx, 0)
                    sheet.cell_value(row_idx, 1)
                    sheet.cell_value(row_idx, 2)
                    license_plate = sheet.cell_value(row_idx, 3)
                    sheet.cell_value(row_idx, 4)
                    sheet.cell_value(row_idx, 5)
                    fleet_number = sheet.cell_value(row_idx, 6)
                    work = sheet.cell_value(row_idx, 7)
                    category = sheet.cell_value(row_idx, 8)
                    sheet.cell_value(row_idx, 9)
                    sheet.cell_value(row_idx, 10)
                    total_value = sheet.cell_value(row_idx, 11) or sheet.cell_value(
                        row_idx, 12
                    )
                    liters = 1.0
                    price_per_liter = total_value
                    fuel_type = f"PEDAGIO - {category}" if category else "PEDAGIO"
                    driver = ""
                    odometer = 0.0
            except IndexError:
                continue

            if not license_plate:
                continue

            license_plate = self._normalize_plate(license_plate)
            driver = str(driver).strip() if driver else ""
            work = str(work).strip() if work else ""

            vehicle = self._find_vehicle(license_plate)
            driver_partner = self._find_driver(driver) if driver else False
            analytic_account = self._find_analytic_account(work)
            product = self._find_product(fuel_type)

            is_valid = True
            error_message = ""

            if not vehicle:
                is_valid = False
                error_message = f"Vehicle with plate {license_plate} not found"
                errors.append(f"Row {row_idx + 1}: {error_message}")
            elif not analytic_account:
                is_valid = False
                error_message = f"Analytic account for work '{work}' not found"
                errors.append(f"Row {row_idx + 1}: {error_message}")
            elif driver and not driver_partner:
                is_valid = False
                error_message = f"Driver '{driver}' not found"
                errors.append(f"Row {row_idx + 1}: {error_message}")
            elif not product:
                is_valid = False
                error_message = f"Product '{fuel_type}' not found"
                errors.append(f"Row {row_idx + 1}: {error_message}")

            line_data = {
                "wizard_id": self.id,
                "row_number": row_idx + 1,
                "date": self._parse_date(date),
                "license_plate": license_plate,
                "fleet_number": fleet_number,
                "work": work,
                "driver_name": driver,
                "fuel_type": fuel_type,
                "liters": self._convert_float(liters),
                "price_per_liter": self._convert_float(price_per_liter),
                "odometer": self._convert_float(odometer),
                "total_value": self._convert_float(total_value),
                "vehicle_id": vehicle.id if vehicle else False,
                "driver_id": driver_partner.id if driver_partner else False,
                "product_id": product.id if product else False,
                "analytic_account_id": analytic_account.id
                if analytic_account
                else False,
                "is_valid": is_valid,
                "error_message": error_message,
            }

            preview_lines |= self.env["ticket.log.wizard.line"].create(line_data)

        self.preview_line_ids = preview_lines
        self.state = "preview"

        if errors:
            error_summary = "\n".join(errors[:50])
            if len(errors) > 50:
                error_summary += f"\n... and {len(errors) - 50} more errors"
            self.error_summary = error_summary
        else:
            self.error_summary = ""

        return {
            "type": "ir.actions.act_window",
            "res_model": "ticket.log.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _create_order_line_data(self, line):
        """Build purchase order line data dictionary.

        :param line: Valid preview line wizard record
        :return: Dictionary for purchase order line
        """
        product = line.product_id
        total = line.liters * line.price_per_liter
        if total <= 0:
            total = line.total_value

        order_line_data = {
            "product_id": product.id,
            "product_qty": line.liters,
            "price_unit": line.price_per_liter,
            "name": "Ticket Log - {} - {} - {}".format(
                line.fuel_type,
                line.license_plate,
                line.driver_name or "No driver",
            ),
            "date_planned": line.date,
            "analytic_distribution": {line.analytic_account_id.id: 100}
            if line.analytic_account_id
            else False,
        }
        if line.vehicle_id:
            order_line_data["fleet_vehicle_id"] = line.vehicle_id.id
        return order_line_data

    def _create_vehicle_odometer(self, line):
        """Create odometer record for vehicle if needed.

        :param line: Valid preview line wizard record
        """
        if self.import_type == "fuel" and line.odometer > 0 and line.vehicle_id:
            odometer_exist = self.env["fleet.vehicle.odometer"].search(
                [
                    ("vehicle_id", "=", line.vehicle_id.id),
                    ("value", "=", line.odometer),
                ],
                limit=1,
            )
            if not odometer_exist:
                self.env["fleet.vehicle.odometer"].create(
                    {
                        "vehicle_id": line.vehicle_id.id,
                        "driver_id": line.driver_id.id,
                        "value": line.odometer,
                        "date": line.date,
                        "refueling_cost": line.total_value,
                    }
                )

    def _update_vehicle_driver(self, line):
        """Update vehicle driver if different from current.

        :param line: Valid preview line wizard record
        """
        if line.driver_id and line.vehicle_id:
            if line.vehicle_id.driver_id != line.driver_id:
                line.vehicle_id.write(
                    {
                        "driver_id": line.driver_id.id,
                    }
                )

    def _get_source_hash(self, line):
        """Generate MD5 hash for duplicate detection.

        :param line: Valid preview line wizard record
        :return: MD5 hash string
        """
        return self._compute_hash(
            {
                "date": str(line.date),
                "license_plate": line.license_plate,
                "driver_name": line.driver_name,
                "fuel_type": line.fuel_type,
                "liters": line.liters,
                "price_per_liter": line.price_per_liter,
                "odometer": line.odometer,
            }
        )

    def _create_import_history(self, line, order, order_line, idx, lines_created):
        """Create import history record for validated line.

        :param line: Valid preview line wizard record
        :param order: Created purchase order
        :param order_line: Related order line created
        :param idx: Line index
        :param lines_created: All created order lines
        """
        if idx >= len(lines_created):
            return

        source_hash = self._get_source_hash(line)
        duplicate = self._check_duplicate(source_hash)
        if not duplicate:
            self.env["ticket.log.import.line"].create(
                {
                    "import_type": self.import_type,
                    "purchase_order_id": order.id,
                    "purchase_order_line_id": lines_created[idx].id,
                    "vehicle_id": line.vehicle_id.id,
                    "license_plate": line.license_plate,
                    "transaction_date": line.date,
                    "driver_name": line.driver_name,
                    "driver_id": line.driver_id.id if line.driver_id else False,
                    "product_name": line.fuel_type,
                    "product_id": line.product_id.id,
                    "quantity": line.liters,
                    "price_unit": line.price_per_liter,
                    "total_value": line.total_value,
                    "odometer_value": line.odometer,
                    "analytic_account_id": line.analytic_account_id.id
                    if line.analytic_account_id
                    else False,
                    "source_hash": source_hash,
                }
            )

    def action_import(self):
        """Create purchase order with validated lines.

        Creates PO, order lines with analytic distribution,
        odometer records for fuel imports, updates vehicle driver.
        Records import history to prevent duplicates.
        Sets state to 'done' on completion.
        :return: Wizard form reload action
        """
        self.ensure_one()
        if not self.preview_line_ids:
            raise UserError(_("No lines to import."))

        valid_lines = self.preview_line_ids.filtered(lambda line: line.is_valid)
        invalid_lines = self.preview_line_ids.filtered(lambda line: not line.is_valid)

        if invalid_lines:
            error_msgs = invalid_lines.mapped("error_message")
            raise UserError(
                _("%(count)d line(s) with error(s):\n%(errors)s")
                % {"count": len(invalid_lines), "errors": "\n".join(error_msgs[:10])}
            )

        if not valid_lines:
            raise UserError(_("No valid lines to import."))

        partner = self.partner_id
        if not partner:
            raise UserError(_("No vendor found."))

        order_lines = []

        for line in valid_lines:
            product = line.product_id
            if not product:
                raise UserError(_("Product not found for: %s") % line.fuel_type)

            source_hash = self._get_source_hash(line)

            duplicate = self._check_duplicate(source_hash)
            if duplicate:
                _logger.info(f"Skipping duplicate line: {source_hash}")
                continue

            order_line_data = self._create_order_line_data(line)
            order_lines.append((0, 0, order_line_data))

            self._create_vehicle_odometer(line)
            self._update_vehicle_driver(line)

        if order_lines:
            order = self.env["purchase.order"].create(
                {
                    "partner_id": partner.id,
                    "date_order": fields.Datetime.now(),
                    "name": "Ticket Log Import - %s" % fields.Date.today(),
                }
            )
            order.write({"order_line": order_lines})
            self.order_count = len(order_lines)

            lines_created = self.env["purchase.order.line"].search(
                [
                    ("order_id", "=", order.id),
                ],
                order="id asc",
            )

            for idx, line in enumerate(valid_lines):
                self._create_import_history(line, order, None, idx, lines_created)

        self.state = "done"
        return {
            "type": "ir.actions.act_window",
            "res_model": "ticket.log.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_reset(self):
        """Reset wizard state to draft and clear error summary.

        :return: Wizard form reload action
        """
        self.state = "draft"
        self.error_summary = ""
        return {
            "type": "ir.actions.act_window",
            "res_model": "ticket.log.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
