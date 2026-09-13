# Design - Rechecagem live CJF/TRF1

Uma abertura GET controlada e suficiente para classificar a superficie quando
a propria pagina publica exibe desafio de acesso. O hash SHA-256, tamanho,
tipo MIME, URL final e marcadores sao preservados; o corpo nao e versionado.
Como o contrato JSF depende de ViewState obtido da sessao, nenhum POST e feito
quando o GET nao entrega formulario/resultados confiaveis.
