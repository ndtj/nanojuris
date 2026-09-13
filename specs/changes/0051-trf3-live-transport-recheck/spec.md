# 0051 - Rechecagem live de transporte do TRF3

Status: verified
Owner: Provider Research, QA e Security

## Intencao

Atualizar a evidencia do candidato `trf3_jurisprudencia` sem transformar
timeout em lista vazia e sem promover um adapter sem contrato reproduzivel.

## Requisitos

- REQ-001: testar somente rotas oficiais publicas e bounded, sem credenciais;
- REQ-002: registrar metodo, URL, timeout, classificacao e ausencia de corpo;
- REQ-003: distinguir `blocked_transport` de HTTP vazio, erro HTTP e acesso;
- REQ-004: manter TRF3 fora do runtime/federacao enquanto nao houver resposta
  juridica, fixture de sucesso e parser canonicamente testado;
- REQ-005: atualizar o dossie canonico e a copia de compatibilidade em paridade;
- REQ-006: nao repetir indefinidamente a mesma chave de timeout.

## Criterios de aceite

- AC-001: as tres superficies alternativas ficam registradas no artefato JSON;
- AC-002: nenhuma falha de transporte e apresentada como zero resultados;
- AC-003: o catalogo continua classificando TRF3 como candidato;
- AC-004: paridade documental, SDD e gates locais passam;
- AC-005: nenhum deploy, push ou acesso autenticado e realizado.

## Fora de escopo

Captura HAR, bypass de Akamai/WAF, login, implementação de parser, criação de
fixture de sucesso e promoção do TRF3.
