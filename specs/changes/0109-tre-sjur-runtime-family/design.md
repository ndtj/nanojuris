# Design — SJUR/TRE runtime family

O cliente padrão instancia uma única `TreSjurJurisprudenciaFamilyProvider`.
Ela cria adapters específicos sob demanda, indexados pela autoridade
normalizada, e compartilha a sessão configurada e o transporte público oficial.

O capability contract permanece deliberadamente opt-in. Isso permite que uma
chamada explicita (`sources=["tre_sjur_jurisprudencia"]` com a fonte autorizada
chamada explícita (`sources=["tre_sjur_jurisprudencia"]` com a fonte autorizada
na configuração) seja diagnosticável sem fazer a busca adaptativa chamar 27
rotas eleitorais ou interpretar uma janela única como coleção completa.

O lifecycle `implemented` neste SDD significa binding executável e descobrível
em runtime; não significa `federation_enabled`. O gerador de cobertura mantém
essas dimensões separadas.
