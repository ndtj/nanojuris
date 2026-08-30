# Threat model

O risco principal é consumir evidência incompleta ou corrompida como se fosse
válida. A troca atômica reduz leituras parciais; o cache miss força nova
verificação. Arquivos continuam limitados ao diretório configurado pelo
usuário e não contêm segredos por design.
