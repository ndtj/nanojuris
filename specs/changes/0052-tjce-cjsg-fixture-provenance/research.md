# Pesquisa - Fixture dedicada TJCE/CJSG

O teste anterior reutilizava `tjsp_cjsg_result.html`, fazendo o tribunal e os
processos parecerem TJSP apesar de o provider emitir identidade TJCE. A nova
fixture usa numeração `8.06`, comarca cearense e valores sintéticos, mantendo
somente a estrutura necessária ao parser CJSG compartilhado.
