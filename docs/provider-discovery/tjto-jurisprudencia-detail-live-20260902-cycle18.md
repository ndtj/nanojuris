# TJTO jurisprudência — busca e detalhe live bounded (2026-09-02)

Sem credenciais, uma busca pública retornou uma decisão e total remoto de 54.936.
O enriquecimento explícito `fetch_details=True` carregou o inteiro teor pela rota
oficial `documento.php` como HTML (381.857 bytes). O corpo jurídico não foi
persistido; o artefato JSON contém somente metadados e hash.

O erro de detalhe não interrompe a busca: o resultado base permanece disponível
com `extraction_status=partial` e `detail_error_type` quando a fonte responde
403, timeout, schema drift ou outro erro controlado. A evidência não altera
produção nem promoção de release.
