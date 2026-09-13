# Design - Estados TJRJ/eproc

As fixtures sao HTML minimo e sanitizado. A fixture vazia contem o marcador
`frmJurisprudenciaPesquisa`, que e o sinal necessario para o parser classificar
uma pagina publica sem cards como zero resultados. A fixture de acesso contem
marcadores de CAPTCHA/Cloudflare e nenhum formulario de resultados; o parser
deve interromper com `AccessControlRequiredError`.
