# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _update_repartition_lines(self, account_id, refund_account_id):
        """Ajusta o fator das linhas de reembolso mesmo sem conta mapeada.

        O l10n_br_coa só ajusta o fator da linha de reembolso dentro de
        ``if refund_account_id:``. Como o plano de contas da Eiras não mapeia
        contas por grupo de imposto, os impostos dedutíveis e retidos ficavam
        com -100% na distribuição para faturas e +100% na distribuição para
        reembolsos.
        """
        res = super()._update_repartition_lines(account_id, refund_account_id)
        if not refund_account_id:
            for tax in self:
                refund_repartition_line = tax.refund_repartition_line_ids.filtered(
                    lambda line: line.repartition_type == "tax"
                )
                # Só ajusta a configuração padrão (uma única linha de imposto),
                # para não sobrescrever repartições customizadas.
                if len(refund_repartition_line) == 1:
                    refund_repartition_line.factor_percent = (
                        -100 if tax.deductible or tax.withholdable else 100
                    )
        return res
