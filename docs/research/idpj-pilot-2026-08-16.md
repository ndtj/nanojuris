# Piloto Jurimétrico: Incidente de Desconsideração da Personalidade Jurídica

**Data da execução:** 2026-08-16
**Run local:** `run-30a571f5039a49e3ac7f1fa16092a096`
**Store local:** `idpj-pilot-20260816`
**Consulta:** `incidente de desconsideração da personalidade jurídica`

## Objetivo

Testar o protocolo de pesquisa jurimétrica do NanoJuris com fontes públicas de
jurisprudência, preservando a distinção entre resultado, bloqueio, alteração de
contrato e ausência de completude.

Esta rodada é um piloto metodológico. Ela não estima a frequência nacional de
decisões sobre IDPJ e não permite afirmar taxa de provimento, prevalência de
tese ou comportamento de todos os tribunais brasileiros.

## Protocolo

Foram consultadas explicitamente pelo MCP:

- `tjdf_juris`;
- `trf4_eproc_jurisprudencia`;
- `stj_scon`;
- `tjsp_cjsg`.

Parâmetros:

```text
page=1
page_size=10
canonical=true
store_id=idpj-pilot-20260816
```

O resultado foi persistido com `search_unified_store`. A janela federada foi
deduplicada antes da paginação. O total observado nesta execução não representa
uma coleta exaustiva.

## Resultado operacional

| Fonte | Retornados na janela da fonte | Total informado pela fonte | Estado |
| --- | ---: | ---: | --- |
| TJDFT | 10 | 4.530 | parcial |
| STJ/SCON | 10 | 963 | desconhecido quanto à completude |
| TRF4/eproc | 0 | não informado | contrato incompatível com o parser |
| TJSP/CJSG | 0 | não informado | controle de acesso/CAPTCHA |

O run federado registrou:

- `deduplicated_total`: 20;
- `total_returned`: 10;
- registros persistidos: 10;
- `collection_complete`: `false`;
- `sources_complete`: nenhuma;
- `sources_partial`: TJDFT, TRF4/eproc e TJSP/CJSG;
- `sources_unknown`: STJ/SCON.

Os dez registros persistidos foram oito do TJDFT e dois do STJ. Todos foram
classificados como acórdãos e possuíam resumo, URL e traces de origem e
extração. Nenhum carregou texto integral automaticamente na busca, conforme o
contrato de carregamento sob demanda.

## Verificação de inteiro teor

Dois documentos foram carregados individualmente pelo MCP, sem contornar
controle de acesso:

| Fonte | Registro | Formato | Texto extraído | Bytes | SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| TJDFT | `tjdf-acordao-2155801` | HTML | 17.010 caracteres | 47.473 | `3994874897160e4091b6160b288e11f780d86c2c08a498b6c654678b8a8ce5db` |
| STJ/SCON | `stj-scon-202500166988` | PDF | 13.362 caracteres | 113.077 | `83da9419356eebfa96c97e7e2bac21b6291dbdd33879e42c201d6bd880d7342a` |

Nos dois casos, o MCP informou `access_status=public` e
`extraction_status=complete`. O teste comprova o contrato desses dois
documentos específicos, não a disponibilidade de inteiro teor para todos os
resultados das fontes.

## Variáveis disponíveis

Na amostra persistida, os registros apresentaram:

- fonte e tribunal;
- identificador estável;
- número do processo;
- classe processual;
- órgão julgador;
- relator;
- data de julgamento;
- data de publicação;
- tipo de decisão;
- ementa/resumo;
- URL oficial;
- `SourceTrace`;
- `ExtractionTrace`;
- campos brutos da fonte.

A codificação de resultado jurídico, fundamento, confusão patrimonial, grupo
econômico, desconsideração inversa e deferimento ainda não foi realizada. Esses
campos devem ser codificados após revisão humana, e não inferidos diretamente
da quantidade de resultados retornados.

## Limitações

1. A amostra efetiva é pequena para inferência estatística.
2. A consulta recuperou apenas a primeira janela federada.
3. O TJDFT respondeu parcialmente diante do total remoto informado.
4. A completude do STJ/SCON permanece desconhecida nesta rodada.
5. O TRF4 exige aprofundamento do contrato do parser.
6. O TJSP/CJSG apresentou controle de acesso e não foi tratado como vazio.
7. A data de publicação dos registros observados está concentrada em 2026;
   isso é efeito da janela atual, não uma tendência histórica.
8. Resultados jurisprudenciais não equivalem ao universo de processos nem
   permitem estimar diretamente probabilidade de êxito.

## Próxima rodada

1. Repetir a consulta com sinônimos e fundamentos: `IDPJ`, `art. 50 do Código
   Civil`, `art. 133 do CPC` e `desconsideração inversa`.
2. Ampliar a coleta por páginas, preservando um run separado por consulta.
3. Validar e corrigir o provider do TRF4 antes de incluí-lo em comparações.
4. Selecionar uma amostra estratificada por fonte, ano e tipo de decisão.
5. Criar as variáveis jurídicas com dupla codificação humana.
6. Medir precisão, duplicidade, concordância entre codificadores e completude
   documental.
7. Só depois executar tabelas comparativas e modelos estatísticos.

## Reprodutibilidade

O run original está salvo no store SQLite local informado acima. A execução
usou MCP local, fontes explícitas, consulta registrada, paginação declarada e
traces por resultado. O relatório deve ser lido junto com os contratos dos
providers e com os estados operacionais retornados pelo MCP.
