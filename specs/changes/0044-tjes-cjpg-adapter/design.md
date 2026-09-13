# Desenho técnico

## Boundary

`TjesCjpgProvider` encapsula a API pública do portal TJES. A configuração
`NanoJurisConfig.tjes_jurisprudencia_url` permite testes e ambientes controlados;
o valor padrão é o domínio oficial. A seleção da coleção fica fixa em
`core=pje1g` para impedir que um caller solicite outro acervo através deste
provider.

## Fluxo

1. validar termo (`text`, `exact_phrase` ou `number`);
2. montar `core`, `q`, `page`, `per_page` e filtros reproduzidos;
3. chamar a rota com `Accept: application/json` e política HTTP compartilhada;
4. classificar o status sem transformar falha em zero resultados;
5. validar raiz, `docs` e `core_used`;
6. normalizar documentos e conservar o payload original em `raw`;
7. calcular janela/completude a partir de `total`, `page` e `per_page`;
8. devolver `SearchPage` com trace e discriminador de primeiro grau.

O inteiro teor é inline em `inteiro_teor`; não existe enriquecimento remoto
promovido. `get_decisions` permanece explicitamente não suportado.

## Segurança e dados

O trace contém apenas parâmetros não sensíveis e metadados do corpo (hash e
tamanho), nunca headers ou credenciais. Fixtures usam IDs e texto sintéticos.
O adapter usa baixa frequência e não persiste resposta live. A revisão de
licença/redistribuição é um gate humano separado do teste técnico.
