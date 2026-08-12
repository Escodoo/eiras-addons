# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests import common

RPS_INFO = {
    "cnpj": "11455184000109",
    "inscricao_municipal": "12345",
    "data_emissao": "2026-08-10T17:50:39",
    "incentivador_cultural": "2",
    "natureza_operacao": "1",
    "optante_simples_nacional": "2",
    "finalidade_emissao": "0",
    "consumidor_final": False,
    "indicador_destinatario": "1",
    "operacao_onerosa": True,
    "status": "1",
}

SERVICE_INFO = {
    "aliquota": 0.03,
    "discriminacao": "SERVICOS DE VIGILANCIA",
    "iss_retido": "1",
    "aliquota_csll": 1.0,
    "aliquota_ir": 1.0,
    "aliquota_inss": 11.0,
    "aliquota_icms": 0,
    "inss_retido": True,
    "ir_retido": True,
    "icms_retido": False,
    "municipio_prestacao_servico": "3512803",
    "item_lista_servico": "705",
    "codigo_cnae": "4223500",
    "valor_servicos": 250.0,
    "valor_liquido_nfse": 211.87,
}

RECIPIENT_INFO = {
    "cnpj": "02709449002950",
    "razao_social": "Petrobras Transporte S.A - Transpetro",
    "email": "suportemedicao@transpetro.com",
    "bairro": "Jardim Mutinga",
    "cep": "06463400",
    "codigo_municipio": 3505708,
    "endereco": "Rodovia Castelo Branco, Km 19,5",
    "numero": "S/N",
    "uf": "SP",
}

BASE_PAYLOAD_KEYS = (
    "prestador",
    "servico",
    "tomador",
    "razao_social",
    "data_emissao",
    "natureza_operacao",
    "finalidade_emissao",
    "indicador_destinatario",
    "status",
)


class TestL10nBrFiscalObra(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.company.city_id = cls.env.ref("l10n_br_base.city_3550308")
        cls.nfse_focus = cls.env["focusnfe.nfse"]
        cls.obra = cls.env["l10n_br_fiscal.obra"].create(
            {
                "name": "Obra Cosmópolis",
                "company_id": cls.company.id,
                "cno_cei": "123456789012",
                "code": "OBR-001",
                "date_start": "2026-01-20",
                "local": "1",
                "street_name": "via sem denominação",
                "street_number": "0",
                "district": "Diversos",
                "zip": "13150970",
            }
        )

    def test_prepare_obra_data(self):
        result = self.obra._prepare_obra_data()

        self.assertEqual(result["cei_cno"], "123456789012")
        self.assertEqual(result["codigo"], "OBR-001")
        self.assertEqual(result["data_inicio"], "20/01/2026")
        self.assertEqual(
            result["endereco"],
            {
                "logradouro": "via sem denominação",
                "numero": "0",
                "complemento": None,
                "bairro": "Diversos",
                "cep": "13150970",
                "epr_ext": None,
            },
        )
        self.assertEqual(result["local"], 1)

    def test_prepare_obra_data_empty_fields(self):
        obra = self.env["l10n_br_fiscal.obra"].create(
            {"name": "Obra Vazia", "company_id": self.company.id}
        )
        result = obra._prepare_obra_data()

        self.assertIsNone(result["cei_cno"])
        self.assertIsNone(result["codigo"])
        self.assertIsNone(result["data_inicio"])
        self.assertEqual(result["local"], 1)

    def test_prepare_service_address_unchanged(self):
        result = self.obra._prepare_service_address()

        self.assertEqual(result["obra_endereco"], "via sem denominação")
        self.assertEqual(result["obra_numero"], "0")
        self.assertEqual(result["obra_bairro"], "Diversos")
        self.assertEqual(result["obra_cep"], "13150970")

    def test_prepare_dados_servico_merges_obra_data(self):
        document = self.env.ref("l10n_br_fiscal.demo_nfse_same_state")
        document.obra_id = self.obra

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document."
            "_prepare_dados_servico",
            return_value={"valor_servicos": 100.0},
        ):
            result = document._prepare_dados_servico()

        self.assertEqual(result["valor_servicos"], 100.0)
        self.assertEqual(result["obra_endereco"], "via sem denominação")
        self.assertEqual(result["obra_data"], self.obra._prepare_obra_data())

    def test_prepare_dados_servico_without_obra_unaffected(self):
        document = self.env.ref("l10n_br_fiscal.demo_nfse_same_state")
        document.obra_id = False

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document."
            "_prepare_dados_servico",
            return_value={"valor_servicos": 100.0},
        ):
            result = document._prepare_dados_servico()

        self.assertEqual(result, {"valor_servicos": 100.0})
        self.assertNotIn("obra_data", result)
        self.assertNotIn("obra_endereco", result)

    def test_prepare_dados_servico_obra_send_data_false(self):
        # Item 7.10 rejects the "obra" block ("Reg50 - O Serviço
        # Informado Não Aceita Dados de Obra") but still needs the
        # address in servico.endereco.
        document = self.env.ref("l10n_br_fiscal.demo_nfse_same_state")
        document.obra_id = self.obra
        document.obra_send_data = False

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document."
            "_prepare_dados_servico",
            return_value={"valor_servicos": 100.0},
        ):
            result = document._prepare_dados_servico()

        self.assertEqual(result["obra_endereco"], "via sem denominação")
        self.assertNotIn("obra_data", result)

    def test_prepare_payload_without_obra(self):
        edoc = [
            {"rps": dict(RPS_INFO)},
            {"service": dict(SERVICE_INFO)},
            {"recipient": dict(RECIPIENT_INFO)},
        ]

        vals = self.nfse_focus._prepare_payload(*edoc, self.company)

        self.assertNotIn("obra", vals)
        for key in BASE_PAYLOAD_KEYS:
            self.assertIn(key, vals)

    def test_prepare_payload_with_obra(self):
        service = dict(SERVICE_INFO)
        service["obra_data"] = self.obra._prepare_obra_data()
        edoc = [
            {"rps": dict(RPS_INFO)},
            {"service": service},
            {"recipient": dict(RECIPIENT_INFO)},
        ]

        vals_with_obra = self.nfse_focus._prepare_payload(*edoc, self.company)

        edoc_without_obra = [
            {"rps": dict(RPS_INFO)},
            {"service": dict(SERVICE_INFO)},
            {"recipient": dict(RECIPIENT_INFO)},
        ]
        vals_without_obra = self.nfse_focus._prepare_payload(
            *edoc_without_obra, self.company
        )

        self.assertIn("obra", vals_with_obra)
        self.assertEqual(vals_with_obra["obra"], service["obra_data"])

        # every other key must stay identical to the base module's own output
        vals_with_obra.pop("obra")
        self.assertEqual(vals_with_obra, vals_without_obra)
