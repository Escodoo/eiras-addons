This module adds an "Obra" (construction site) record with a CNO/CEI code,
an internal code, a start date, a geographic scope ("local") and an
address. The Obra can be selected on the customer invoice, and its data is
sent to Focus NFe in the NFSe Municipal payload as required by some
municipalities for civil construction services:

* The address is sent as the service-provision address
  (``servico.endereco``).
* The CNO/CEI, internal code, start date, address and geographic scope are
  sent in the top-level ``obra`` object (``obra.cei_cno``, ``obra.codigo``,
  ``obra.data_inicio``, ``obra.endereco`` and ``obra.local``), which some
  municipalities require to authorize NFSe with INSS retention for civil
  construction services.
