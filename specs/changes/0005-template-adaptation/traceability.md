# Rastreabilidade da adaptação

| Capacidade local observada | Adaptação NanoJuris | Estado |
| --- | --- | --- |
| `parser.py` / `SelectorsGeneration` | document/node wrappers | adaptado em `nanojuris.parsing` |
| `core/storage.py` | memória de seletores e evidências | adaptado em `nanojuris.adaptive` |
| `spiders/engine.py` / `scheduler.py` | runner de providers | adaptado em `nanojuris.collection` |
| `spiders/checkpoint.py` | checkpoint serializável | adaptado em `nanojuris.collection` |
| `spiders/cache.py` | cache bounded por fingerprint | existente na discovery; coleta usa checkpoint e store |
| `spiders/result.py` | manifestos e métricas | adaptado em `CollectionReport` |
| `fetchers/chrome.py` | browser Playwright opcional | adaptado na discovery |
