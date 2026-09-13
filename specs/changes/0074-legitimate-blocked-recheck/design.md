# Design

O smoke reutiliza os adapters existentes e a sessão pública normal de cada
provider. A lista de classes é declarativa e o relatório é um envelope redigido
contendo somente metadados, hashes e estados. Nenhum token de CAPTCHA é gerado,
resolvido ou armazenado. A promoção federada continua sujeita aos gates já
existentes e é independente da revalidação de disponibilidade.
