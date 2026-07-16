# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestPurchaseRequestAnalyticAccount(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type_id = cls.env.ref("stock.picking_type_in")
        cls.product = cls.env.ref("product.product_product_13")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

        plan = cls.env["account.analytic.plan"].create({"name": "Eiras Test Plan"})
        cls.analytic_account_1 = cls.env["account.analytic.account"].create(
            {"name": "Cost Center 1", "plan_id": plan.id}
        )
        cls.analytic_account_2 = cls.env["account.analytic.account"].create(
            {"name": "Cost Center 2", "plan_id": plan.id}
        )

    def _create_request(self):
        return self.env["purchase.request"].create(
            {
                "picking_type_id": self.picking_type_id.id,
                "requested_by": self.env.user.id,
            }
        )

    def _create_line(self, request, analytic_distribution=None):
        return self.env["purchase.request.line"].create(
            {
                "request_id": request.id,
                "product_id": self.product.id,
                "product_uom_id": self.uom_unit.id,
                "product_qty": 1.0,
                "analytic_distribution": analytic_distribution or {},
            }
        )

    def test_analytic_account_id_without_lines(self):
        request = self._create_request()
        self.assertFalse(request.analytic_account_id)

    def test_analytic_account_id_without_distribution(self):
        request = self._create_request()
        self._create_line(request)
        self.assertFalse(request.analytic_account_id)

    def test_analytic_account_id_takes_first_line(self):
        request = self._create_request()
        self._create_line(request, {str(self.analytic_account_1.id): 100.0})
        self._create_line(request, {str(self.analytic_account_2.id): 100.0})

        self.assertEqual(request.analytic_account_id, self.analytic_account_1)

    def test_analytic_account_id_recomputes_on_first_line_change(self):
        request = self._create_request()
        line = self._create_line(request, {str(self.analytic_account_1.id): 100.0})

        self.assertEqual(request.analytic_account_id, self.analytic_account_1)

        line.analytic_distribution = {str(self.analytic_account_2.id): 100.0}

        self.assertEqual(request.analytic_account_id, self.analytic_account_2)

    def test_group_by_analytic_account_id(self):
        request_a = self._create_request()
        self._create_line(request_a, {str(self.analytic_account_1.id): 100.0})

        request_b = self._create_request()
        self._create_line(request_b, {str(self.analytic_account_2.id): 100.0})

        groups = self.env["purchase.request"].read_group(
            domain=[("id", "in", (request_a + request_b).ids)],
            fields=["analytic_account_id"],
            groupby=["analytic_account_id"],
        )
        grouped_ids = {
            group["analytic_account_id"][0]
            for group in groups
            if group["analytic_account_id"]
        }

        self.assertEqual(
            grouped_ids, {self.analytic_account_1.id, self.analytic_account_2.id}
        )
