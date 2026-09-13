# Tarefas

- [x] T01 - inventariar capacidades documentais por provider.
- [x] T02 - definir DocumentReference e contrato de fetch.
- [x] T03 - implementar download seguro e content-addressed cache.
- [x] T04 - implementar parsers por formato.
- [x] T05 - vincular CanonicalDocument sem alterar busca padrao.
- [x] T06 - testar limites, corrupcao, redirects e formatos.
- [x] T07 - documentar limites de uso, retencao e limpeza.
- [x] T08 - promover individualmente os providers documentais aprovados pelo manifesto tecnico: TJDF, TJES CJPG/CJSG, TJRN, TJPR, TJRO, TJRS e TJSP CJPG; fontes sem gate permanecem opt-in ou bloqueadas.

O pipeline comum e offline e nao afirma disponibilidade live para providers sem
evidencia. A aprovacao operacional 2026-09-05 cobre runtime local/federado; deploy
e redistribuicao permanecem fora do escopo.
- [x] T09 - rejeitar na fronteira de fetch respostas declaradas como PDF que
  contenham corpo de erro, magic inválido ou estrutura PDF inválida; preservar
  a classificação sanitizada sem colocá-la em cache.
- Escopo de compatibilidade: o fetch rejeita imediatamente o corpo sem magic
  `%PDF-`; documentos truncados que possuem o marcador são preservados para
  diagnóstico e permanecem com `pdf_status` inválido no contrato canônico.
