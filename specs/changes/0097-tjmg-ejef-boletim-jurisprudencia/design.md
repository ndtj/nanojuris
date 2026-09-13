# Design

O adapter especializado herda apenas o transporte seguro e a resolução de
bitstreams do adapter DSpace existente. A busca fixa o UUID da coleção EJEF,
evitando misturar itens de outras coleções. O parser compartilha a normalização
de metadados, mas substitui `source`, `collection` e `source_origin` para manter
proveniência independente.

O ranking federado recebe a fonte como jurisprudência curada parcial. O total
é o `totalElements` da consulta DSpace; a interface deve exibir a limitação de
escopo. Não há índice próprio, embeddings ou chamada de IA.
