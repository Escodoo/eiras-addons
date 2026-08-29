# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class L10nBrCoaEiras(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.l10n_br_coa_generic = cls.env.ref(
            "l10n_br_coa_eiras.account_template_eiras"
        )
        cls.l10n_br_company = cls.env["res.company"].create(
            {"name": "Eiras - Chart of Accounts"}
        )

    def test_l10n_br_coa_eiras(self):
        """Test to install the chart of accounts template in a new company"""
        self.env.user.company_ids += self.l10n_br_company
        self.env.user.company_id = self.l10n_br_company
        self.l10n_br_coa_generic.try_loading()

        self.assertEqual(
            self.l10n_br_coa_generic, self.l10n_br_company.chart_template_id
        )

    def test_deductible_and_withholding_taxes_factor(self):
        """Impostos dedutíveis e retidos devem ser criados com -100%"""
        self.env.user.company_ids += self.l10n_br_company
        self.env.user.company_id = self.l10n_br_company
        self.l10n_br_coa_generic.try_loading()

        taxes = (
            self.env["account.tax"]
            .with_context(active_test=False)
            .search(
                [
                    ("company_id", "=", self.l10n_br_company.id),
                    "|",
                    ("deductible", "=", True),
                    ("withholdable", "=", True),
                ]
            )
        )
        self.assertTrue(taxes, "Nenhum imposto dedutível/retido foi criado")

        for tax in taxes:
            repartition_lines = (
                tax.invoice_repartition_line_ids + tax.refund_repartition_line_ids
            ).filtered(lambda line: line.repartition_type == "tax")
            for line in repartition_lines:
                document = "reembolsos" if line.refund_tax_id else "faturas"
                self.assertEqual(
                    line.factor_percent,
                    -100,
                    f"O imposto {tax.name} deveria estar com -100% "
                    f"na distribuição para {document}",
                )
