# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base import misc

from odoo import fields, models


class L10nBrFiscalObra(models.Model):
    _name = "l10n_br_fiscal.obra"
    _description = "Obra (Construction Site)"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    cno_cei = fields.Char(
        string="CNO/CEI",
        help="Cadastro Nacional de Obras / Cadastro Específico do INSS",
    )
    civil_construction_art = fields.Char(string="ART")
    street_name = fields.Char(string="Street")
    street_number = fields.Char(string="Number")
    street_number2 = fields.Char(string="Complement")
    district = fields.Char()
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        domain="[('country_id.code', '=', 'BR')]",
    )
    city_id = fields.Many2one(
        comodel_name="res.city",
        string="City",
        domain="[('state_id', '=', state_id)]",
    )
    zip = fields.Char()

    def _prepare_service_address(self):
        self.ensure_one()
        return {
            "obra_endereco": str(self.street_name or ""),
            "obra_numero": self.street_number or "",
            "obra_complemento": self.street_number2 or "",
            "obra_bairro": str(self.district or ""),
            "obra_codigo_municipio": (
                int(self.city_id.ibge_code) if self.city_id.ibge_code else False
            ),
            "obra_uf": self.state_id.code or "",
            "obra_cep": (misc.punctuation_rm(self.zip).zfill(8) if self.zip else ""),
        }
