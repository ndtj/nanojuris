# Research

- A documentação oficial da OCI descreve provisioned concurrency para manter
  infraestrutura disponível e reduzir a latência inicial:
  https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingprovisionedconcurrency.htm
- O provider Terraform OCI documenta `provisioned_concurrency_config` com
  `strategy` e `count`:
  https://docs.oracle.com/en-us/iaas/tools/terraform-provider-oci/latest/docs/r/functions_function.html
- O repositório atualmente fixa `oracle/oci` em 7.32.0, versão compatível com
  o bloco acima.
