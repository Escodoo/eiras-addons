# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class FocusnfeNfse(models.AbstractModel):
    _inherit = "focusnfe.nfse"

    def _prepare_service_data(self, service, company):
        result = super()._prepare_service_data(service, company)
        if service.get("obra_endereco"):
            result["endereco"] = {
                "logradouro": service.get("obra_endereco"),
                "numero": service.get("obra_numero"),
                "complemento": service.get("obra_complemento") or None,
                "bairro": service.get("obra_bairro"),
                "codigo_municipio": service.get("obra_codigo_municipio"),
                "uf": service.get("obra_uf"),
                "cep": service.get("obra_cep"),
            }
        return result

    def _prepare_payload(self, rps, service, recipient, company):
        vals = super()._prepare_payload(rps, service, recipient, company)
        obra_data = (service.get("service") or {}).get("obra_data")
        if obra_data:
            vals["obra"] = obra_data
        return vals
