# Design - Fixture HTML dedicada TJRJ/eproc

O HTML segue a estrutura publica eproc ja consumida pelo parser comum, mas usa
identificador e processo ficticios, UF `RJ` e dominio `eproc1g.tjrj.jus.br` nas
URLs. Labels sao ASCII para tornar o replay estavel entre codificacoes. O
teste continua passando o dominio TJRJ na resposta fake, portanto a fixture
prova mapeamento de estrutura, nao disponibilidade live.
