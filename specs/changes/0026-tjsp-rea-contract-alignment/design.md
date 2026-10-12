# Design

## Decisões

1. A configuração eproc muda somente o default para o entry point oficial
   atualmente observado. `NanoJurisConfig` continua permitindo override por
   instância e ambiente conforme o contrato existente.
2. O CJSG usa tabelas fechadas para origem e ordenação. Valores desconhecidos
   não são inventados; permanecem no fluxo anterior ou são omitidos conforme o
   filtro não tenha tradução segura.
3. A cadeia documental CJSG é um fallback compatível com o navegador: após uma
   resposta de verificação, o provider chama a página de verificação e repete
   a rota com `casChecked=true`. A cadeia não envia credenciais, não resolve
   CAPTCHA e continua sujeita às mesmas detecções de acesso.
4. O eproc mantém paginação serializada do formulário de resultados e passa a
   declarar as rotas auxiliares observadas. Não será criado um scraper de
   endpoints internos sem contrato de resposta.
5. A documentação derivada é regenerada pelos scripts oficiais; catálogos não
   são editados manualmente.

## Dados e rastreabilidade

Os SourceTrace existentes continuam registrando endpoint, payload, URL final,
hash, tamanho e status. A sequência documental adiciona os endpoints usados e
mantém o último response como fonte do documento, evitando misturar uma tela de
login com conteúdo jurídico.

## Segurança

O bloqueio é fail-closed. CAPTCHA, login, WAF, HTTP 401/403/429 e telas de
controle de acesso não são tratados como vazio. A cadeia `casChecked=true` só
reproduz uma etapa pública já observada e não autoriza qualquer tentativa de
adivinhar, reutilizar ou fabricar tokens.
