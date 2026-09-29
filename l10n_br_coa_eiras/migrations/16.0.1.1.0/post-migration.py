# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _fix_tax_repartition_factor(env):
    """Corrige o fator das linhas de distribuição dos impostos já criados.

    Os impostos dedutíveis e retidos foram criados com +100% porque o plano de
    contas da Eiras não trazia os registros de
    ``l10n_br_coa.account.tax.group.account.template``, que é o gatilho usado
    pelo l10n_br_coa para inverter o sinal. Todos devem estar com -100%.
    """
    taxes = (
        env["account.tax"]
        .with_context(active_test=False)
        .search(["|", ("deductible", "=", True), ("withholdable", "=", True)])
    )

    fixed = env["account.tax"].browse()
    for tax in taxes:
        for lines in (
            tax.invoice_repartition_line_ids,
            tax.refund_repartition_line_ids,
        ):
            tax_lines = lines.filtered(lambda line: line.repartition_type == "tax")
            # Só ajusta a configuração padrão (uma única linha de imposto),
            # para não sobrescrever repartições customizadas.
            if len(tax_lines) != 1 or tax_lines.factor_percent != 100:
                continue
            tax_lines.factor_percent = -100
            fixed |= tax

    _logger.info(
        "l10n_br_coa_eiras: %s de %s impostos dedutíveis/retidos corrigidos "
        "para -100%% nas linhas de distribuição.",
        len(fixed),
        len(taxes),
    )
    if fixed:
        _logger.debug(
            "l10n_br_coa_eiras: impostos corrigidos: %s",
            ", ".join(f"{tax.company_id.name}/{tax.name}" for tax in fixed),
        )


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _fix_tax_repartition_factor(env)
