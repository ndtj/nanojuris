# Threat model

## Riscos

- HTML malformado ou muito grande pode causar custo de CPU/memória.
- Um seletor semelhante pode capturar campo jurídico errado.
- Checkpoint corrompido pode perder continuidade ou duplicar lote.
- Coletas longas podem tratar bloqueio como vazio se o contrato for fraco.

## Controles

- Limites de bytes, páginas, profundidade e tempo continuam obrigatórios.
- Similaridade gera sugestão com confiança e evidência, nunca alteração automática.
- Checkpoint usa esquema versionado e escrita atômica.
- AccessStatus, SourceTrace e ExtractionTrace permanecem obrigatórios.
- O código de stealth, rotação de proxy e automação de desafios fica fora do
  núcleo do NanoJuris.
