# Threat model - TJAC Ementario

## Ativos

URL oficial, bytes do PDF, texto extraido, identificadores CNJ e traces.

## Ameacas

- PDF malformado ou excessivamente grande;
- redirecionamento para host nao oficial;
- documento imagem-only ou texto corrompido;
- falsa interpretacao de vazio como bloqueio;
- inclusao acidental de consulta processual.

## Controles

HTTPS e allowlist, limites de bytes/paginas, parser conservador, rejeicao de
identidade ausente, `total_unknown`, sem OCR automatico, sem seguir links de
consulta processual e estados de erro preservados.
