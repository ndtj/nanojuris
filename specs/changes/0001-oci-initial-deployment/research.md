# Pesquisa - Implantacao inicial OCI

Mudanca: `0001-oci-initial-deployment`
Data da revisao: `2026-08-20`
Status: `completed`

## Pergunta de pesquisa

Quais praticas atuais tornam uma mudanca SDD, uma aplicacao web e sua operacao
OCI mais verificaveis, seguras e evolutivas sem aumentar complexidade antes da
necessidade?

## Fontes primarias

| Fonte | Achado aplicado | Decisao influenciada | Confianca |
| --- | --- | --- | --- |
| GitHub Spec Kit, `spec-driven.md` | especificacao e fonte primaria; pesquisa, refinamento e feedback sao continuos | adicionar pesquisa, clarificacao e rastreabilidade | alta |
| Microsoft for Developers, SDD AI-native engineering | fluxo Constitution -> Specify -> Clarify -> Plan -> Tasks -> Implement -> Validate | explicitar clarify e gates humanos | alta |
| NIST SP 800-218 SSDF | seguranca deve integrar o ciclo de desenvolvimento | threat model e gate de supply chain | alta |
| Google SRE Book, SLOs | SLIs/SLOs mensuraveis e error budget orientam releases | criar `service-levels.md` | alta |
| C4 Model | contexto, containers e implantacao sao visoes uteis e hierarquicas | exigir consistencia arquitetural | alta |
| OWASP ASVS 5.0 | requisitos verificaveis para controles tecnicos de aplicacoes web | fortalecer revisao de seguranca | alta |
| OCI Resource Manager, DevOps, Registry, Secrets e Audit | infraestrutura, entrega, artefatos, segredos e auditoria tem servicos proprios | manter infra separada e evidencias por gate | alta |

## URLs consultadas

- https://github.com/github/spec-kit/blob/main/spec-driven.md
- https://developer.microsoft.com/blog/spec-driven-development-ai-native-engineering/
- https://csrc.nist.gov/pubs/sp/800/218/final
- https://sre.google/sre-book/service-level-objectives/
- https://c4model.com/
- https://owasp.org/www-project-application-security-verification-standard/
- https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Concepts/resourcemanager.htm
- https://docs.oracle.com/en-us/iaas/Content/devops/using/devops_overview.htm
- https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryoverview.htm
- https://docs.oracle.com/en-us/iaas/Content/secret-management/overview.htm
- https://docs.oracle.com/en-us/iaas/Content/Audit/home.htm

## Sintese

O material existente ja adotava constituicao, mudanca versionada, aprovacao
humana e separacao app/infra. O principal ganho de maturidade nao e adicionar
mais servicos, mas fechar o ciclo entre intencao, risco, implementacao, teste,
operacao e aprendizado.

## Limitacoes

- custos, regiao, dominio, trafego e perfil de carga da OCI ainda nao foram confirmados;
- os SLOs sao candidatos e precisam de dados reais;
- Compute versus Container Instance continua uma decisao pendente;
- nenhuma chamada real a OCI foi executada nesta revisao.
