"""Generate reviewable SDD drafts from discovery evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nanojuris.discovery.models import DiscoveryRun


def build_sdd_artifacts(run: DiscoveryRun) -> dict[str, str]:
    metrics = run.metrics()
    statuses = ", ".join(f"`{key}`={value}" for key, value in metrics["statuses"].items()) or "nenhum"
    routes = sorted({candidate.url for evidence in run.evidences for candidate in evidence.route_candidates})
    selectors = [candidate for evidence in run.evidences for candidate in evidence.selector_candidates]
    route_lines = "\n".join(f"- `{route}`" for route in routes) or "- Nenhuma rota candidata registrada."
    selector_lines = "\n".join(
        f"- `{candidate.field}`: `{candidate.selector}` ({candidate.confidence:.2f}; {candidate.evidence})"
        for candidate in selectors
    ) or "- Nenhum seletor candidato registrado."
    return {
        "research.md": f"""# Pesquisa de descoberta\n\nRun: `{run.run_id}`\n\n## Observações\n\n- Observações: {metrics['observations']}\n- Bytes: {metrics['response_bytes']}\n- Estados: {statuses}\n\n## Rotas candidatas\n\n{route_lines}\n\n## Limitações\n\n- Esta execução é evidência de descoberta, não confirmação de provider.\n- A fonte, o contrato e as fixtures ainda precisam de revisão humana.\n""",
        "clarify.md": """# Perguntas de esclarecimento\n\n- A rota candidata é oficial e pública?\n- O método, payload, filtros, paginação e ordenação foram confirmados?\n- Quais estados de vazio, query inválida, bloqueio e indisponibilidade foram observados?\n- O conteúdo textual atende ao escopo de jurisprudência pública?\n""",
        "spec.md": f"""# Rascunho de especificação de provider\n\nStatus: `draft`\nRun: `{run.run_id}`\n\n## Intenção\n\nTransformar as evidências abaixo em um contrato de provider revisado.\n\n## Rotas observadas\n\n{route_lines}\n\n## Requisitos pendentes\n\n- [ ] Fonte oficial e entrada pública confirmadas.\n- [ ] Método, payload, filtros, paginação e ordenação confirmados.\n- [ ] Estados operacionais testados sem converter bloqueio em vazio.\n- [ ] Identidade, datas, texto e campos brutos definidos.\n- [ ] Fixture pública minimizada e parser offline criado.\n""",
        "design.md": """# Rascunho de design\n\n- Usar o adapter mais simples que reproduza a rota observada.\n- Preservar `SourceTrace` e `ExtractionTrace`.\n- Manter a evidência original separada do parser canônico.\n- Não promover seletores candidatos sem fixtures e testes.\n""",
        "tasks.md": """# Tarefas derivadas\n\n- [ ] Validar autoridade e escopo da fonte.\n- [ ] Reproduzir a rota com fixture ou captura minimizada.\n- [ ] Implementar parser e normalização canônica.\n- [ ] Cobrir sucesso, vazio, inválido, timeout, bloqueio e mudança.\n- [ ] Atualizar dossier, source contract e catálogo gerado.\n""",
        "verification.md": """# Plano de verificação\n\n- Reprocessar a evidência offline.\n- Comparar hash e campos extraídos com as fixtures.\n- Executar testes de contrato e documentação.\n- Executar validação bounded opcional somente após aprovação.\n""",
        "traceability.md": f"""# Rastreabilidade\n\n- Run: `{run.run_id}`\n- Métricas: `{json.dumps(metrics, ensure_ascii=False, sort_keys=True)}`\n- Cada observação deve ser referenciada pelo seu hash de conteúdo no pacote de evidências.\n""",
        "threat-model.md": """# Threat model da descoberta\n\n- Allowlist e limites devem ser preservados.\n- Payloads e headers sensíveis devem permanecer redigidos.\n- Bloqueios e controles de acesso devem ser publicados como estado explícito.\n- O draft não tem autoridade para alterar provider ou catálogo.\n""",
        "selector-candidates.md": f"""# Candidatos de seletores\n\n{selector_lines}\n\nTodos os candidatos exigem revisão e validação em múltiplas fixtures.\n""",
    }


def write_sdd_artifacts(run: DiscoveryRun, directory: str | Path, *, include_body: bool = True) -> Path:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    (target / "evidence.json").write_text(
        json.dumps(run.to_dict(include_body=include_body), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for name, content in build_sdd_artifacts(run).items():
        (target / name).write_text(content, encoding="utf-8")
    return target
