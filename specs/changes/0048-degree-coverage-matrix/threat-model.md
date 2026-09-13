# Threat model

- **Falsa cobertura:** uma linha equivalente não pode inflar CJPG/CJSG; a
  validação exige coleção e grau específicos.
- **Confusão de ramo:** autoridade, ramo e unidade judicial são campos
  independentes; nomes parecidos não promovem uma fonte para outra hierarquia.
- **Acesso controlado:** CAPTCHA, WAF, login, TLS e rate limit permanecem como
  status explícitos, sem fallback para vazio.
- **Dados pessoais:** a matriz guarda metadados de contrato e IDs de provider,
  não respostas live nem documentos pessoais.
- **Drift:** artefatos têm versão/data de corte; mudanças de catálogo exigem
  regeneração e revisão SDD.
- **Escopo:** linhas de varas, zonas e auditorias são lacunas agregadas, não
  endpoints inventados.
