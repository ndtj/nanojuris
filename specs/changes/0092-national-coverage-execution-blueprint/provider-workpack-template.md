# Workpack por provider

Copie este arquivo para o SDD individual do provider e substitua os campos.

## Identidade

- `source_id`:
- `authority`:
- `branch`:
- `degree`:
- `instance`:
- `collection`:
- `surface_id`:
- `owner`:

## Descoberta

- fonte oficial e URL de entrada:
- rota/API/export:
- método e payload:
- origem da descoberta no Juscraper (commit/licença):
- diferença em relação ao Juscraper:
- termos/robots/rate limit:

## Contrato

- filtros remotos:
- filtros traduzidos:
- filtros locais:
- filtros ignorados/não suportados:
- paginação, cursor e ordenação:
- campos canônicos:
- campos `raw`:
- estados de acesso/extração:
- detalhe e documento:

## Evidência bounded

- comando/data:
- request redigido:
- status HTTP/content type/bytes:
- classificação:
- `evidence_id`:
- limites e TTL:

## Fixtures e testes

- sucesso:
- segunda página:
- vazio autoritativo:
- vazio não confirmado:
- parâmetro inválido:
- bloqueio/erro externo:
- schema drift:
- deduplicação e identidade:

## Promoção

Marque cada gate no `promotion-gate.schema.json`. Se um gate falhar, não
habilite federação e registre a próxima ação objetiva.
