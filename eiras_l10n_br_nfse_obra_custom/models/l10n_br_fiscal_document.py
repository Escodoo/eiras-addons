# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nBrFiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    obra_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.obra",
        string="Obra",
        domain="[('company_id', '=', company_id)]",
    )
    obra_send_data = fields.Boolean(
        string="Enviar Dados da Obra",
        default=True,
        help="Alguns itens de serviço/municípios rejeitam o bloco 'obra' no "
        "envio ao Focus NFe, retornando 'Reg50 - O Serviço Informado Não "
        "Aceita Dados de Obra' (ex.: item de lista de serviço 7.10). "
        "Desmarque esta opção nesses casos para continuar enviando o "
        "endereço da Obra em 'servico.endereco', sem enviar o bloco 'obra'.",
    )

    @api.onchange("obra_id")
    def _onchange_obra_id(self):
        if self.obra_id:
            self.civil_construction_code = self.obra_id.cno_cei
            self.civil_construction_art = self.obra_id.civil_construction_art

    def _prepare_dados_servico(self):
        result = super()._prepare_dados_servico()
        if self.obra_id:
            result.update(self.obra_id._prepare_service_address())
            if self.obra_send_data:
                result["obra_data"] = self.obra_id._prepare_obra_data()
        return result
