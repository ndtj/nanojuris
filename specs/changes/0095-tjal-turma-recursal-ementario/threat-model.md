# Threat model

## Ativos

- disponibilidade das fontes oficiais;
- integridade de PDFs e metadados;
- segredos e cookies da plataforma;
- dados pessoais presentes em ementas históricas.

## Riscos e controles

- redirect malicioso: host final deve permanecer allowlisted;
- PDF malformado/zip bomb: limite de bytes e paginas antes de extracao;
- desafio de acesso: classificar como bloqueio e nao automatizar solver;
- identificador ausente: usar ID derivado do hash do volume/pagina, sem afirmar
  equivalencia CNJ;
- excesso de chamadas: uma janela por consulta e rate limit cooperativo.

Nenhum token, cookie persistente ou corpo integral bruto sera armazenado.
