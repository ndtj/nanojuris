# Tarefas

- [x] T00 - executar rechecagem bounded do endpoint oficial sem credenciais;
- [x] T01 - localizar e documentar somente superficies oficiais de acordaos.
- [x] T02 - fechar contrato HTTP e politica de reuso (offset, total, graus,
  divergencia de `tipo`, limites conhecidos e falhas observaveis).
- [x] T03 - criar fixtures sanitizadas e parser canonico (listagem JSON,
  zero autoritativo, identidade e preservacao de campos).
- [x] T04 - testar identidade, pagina, vazio, erro, acesso e schema drift.
- [x] T05 - integrar source ID separado do LIAME e registrar o provider na
  lista padrão da federação, mantendo LIAME como coleção independente.
- [x] T06 - executar validação live bounded de busca, inteiro teor e rota
  relacionada; busca e documento público têm contrato e testes reproduzíveis.
  A rota de facetas foi confirmada, mas aguarda modelo canônico e política de
  retenção antes de entrar no runtime. O ciclo 15 também reproduziu datas,
  relator e o limite observado de `size`.
- [x] T07 - fechar o binding de primeiro grau (CJPG): traduzir
  `degree=first`/`collection=CJPG` para `fields.grau_jurisdicao=[1]`, exigir
  `PJEPG`, validar duas páginas bounded sem sobreposição e testar o download
  de inteiro teor pela combinação observada de `id_processo_documento` e
  `sistema_origem`.

Observação de governança: os gates globais 0031/0034 e um release de produção
continuam fora deste pacote e exigem revisão própria. Esta conclusão habilita o
provider no runtime local/federado, mas não autoriza deploy, push ou publicação.
