# Cache de discovery resiliente

Status: `verified`

## Intenção

Aplicar à cache local de discovery um padrão de escrita atômica e tolerância a
envelopes corrompidos, inspirado no template analisado, sem importar código de
stealth, proxy ou bypass.

## Escopo

- substituir arquivos temporários por `os.replace` após escrita concluída;
- tratar cache ilegível/corrompida como miss recuperável;
- manter a API síncrona existente.

## Fora de escopo

Não inclui alteração de providers, coleta live, rotação de proxy, evasão de
controles ou cópia literal de módulos do template.

## Requisitos e aceite

- **REQ-001**: leitores nunca devem observar JSON parcialmente escrito.
- **REQ-002**: JSON inválido ou ilegível deve resultar em cache miss, não em
  falha da descoberta.
- **REQ-003**: o diretório e arquivos temporários devem ser limpos mesmo após
  erro.
- **AC-001**: teste de escrita/leitura e teste de envelope corrompido passam.
- **AC-002**: Ruff, compilação e suíte completa passam.
