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
    code = fields.Char()
    date_start = fields.Date()
    local = fields.Selection(
        selection=[
            ("1", "Execução no município do prestador"),
            ("2", "Execução fora do município do prestador"),
            ("3", "Execução no exterior"),
        ],
        default="1",
    )

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

    def _prepare_obra_data(self):
        self.ensure_one()
        return {
            "cei_cno": misc.punctuation_rm(self.cno_cei) if self.cno_cei else None,
            "codigo": self.code or None,
            "data_inicio": (
                self.date_start.strftime("%d/%m/%Y") if self.date_start else None
            ),
            "endereco": {
                "logradouro": self.street_name or None,
                "numero": self.street_number or None,
                "complemento": self.street_number2 or None,
                "bairro": self.district or None,
                "cep": (misc.punctuation_rm(self.zip).zfill(8) if self.zip else None),
                "epr_ext": None,
            },
            "local": int(self.local) if self.local else 1,
        }
