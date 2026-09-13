# Design - época única para artefatos derivados

O builder de cobertura continua sendo a fonte dos artefatos gerados. Sua
função de snapshot lê o `generated_at` anterior e os timestamps dos artefatos
live dedicados e dos runs estruturados, escolhendo a maior data ISO válida.
Assim, uma reexecução sem nova evidência é estável e uma evidência posterior
não fica escondida por um timestamp antigo.

A auditoria documental lê a data do catálogo operacional antes de considerar o
relatório anterior. Isso mantém catálogo, dossiês e work packs no mesmo
snapshot sem editar tabelas geradas manualmente.

Artefatos ausentes, ilegíveis ou JSON inválido são ignorados; a geração offline
continua possível e não transforma falha de fonte em sucesso.
