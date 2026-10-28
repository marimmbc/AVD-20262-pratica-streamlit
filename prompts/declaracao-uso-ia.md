# Declaração de Uso de IA

**Nome:** Mariana Correia
**Data:** 28/10/2026 

## Ferramenta

Claude Opus 5.5

## Prompt usado

> veja o que está sendo pedido nesse arquivo para fazer a atividade Streamlit parte 2
> me ajude a fazer o passo a passo solicitado no arquivo pdf


## O que a IA fez

- **Dashboard 1:** moveu os cálculos pesados (filtro por intervalo, matriz de correlação, histograma) para funções com `@st.cache_data` que recebem só os valores dos widgets; colocou a legenda do heatmap embaixo para ele não ficar espremido; testou 0, 1 e 2+ variáveis, os dois métodos de correlação, o toggle por classe e intervalos que zeram a base (sem erros, com avisos nos casos de borda).
- **Identidade visual:** `.streamlit/config.toml` com paleta derivada das cores da EDA (roxo `#2d223a`, rosa `#e9d4d0`, destaque vinho `#8e3b5f`), fontes Nunito Sans (texto) e Lora (títulos), tema claro e escuro; no escuro os gráficos trocam para tons mais claros.
- **Abas:** `st.tabs` separando Dashboard 1 e Dashboard 2.
- **Dashboard 2:** widgets (sexo, faixas etárias, agrupamento), 5 KPIs com `st.metric` e dois gráficos Altair; o clique numa barra filtra os KPIs e o gráfico de IMC (`on_select="rerun"`, exemplo 3 do guia).
- **Entregas:** wireframe `entregas/rascunho-dashboard2.png` (gerado com matplotlib, no mesmo estilo do rascunho 1) e `entregas/justificativa-metricas.md`.

## O que foi aceito, modificado ou rejeitado e por quê

- **Aceito:** a estrutura do Dashboard 2, as 5 métricas e o uso de tabela pré-agregada em cache (o Altair recebe ~80 linhas em vez de 300 mil).
- **Modificado:** _(preencher: o que eu mudei depois de revisar)_
- **Rejeitado:** a primeira versão dos KPIs em 5 colunas fixas, porque os rótulos ficavam cortados em telas estreitas (trocada por uma linha que quebra); a formatação do delta que trocava todos os pontos por vírgulas e estragava "p.p." e "vs.".
