# Justificativa das métricas — Dashboard 2

**Dataset:** Cardiovascular Diseases Risk Prediction (CVD), 308.611 pessoas, já tratado em `data/clean/dataset.csv`.

**Público-alvo geral:** gestores e equipes de saúde pública/atenção primária e o público leigo interessado em prevenção, que não precisam ler histogramas nem matrizes de correlação para entender o risco cardiovascular de um grupo.

**Planejamento (ordem seguida):**

1. **Variáveis selecionadas:** `Heart_Disease` (desfecho), `faixa_etaria`, `sexo_label`, `General_Health`, `Exercise`, `Smoking_History` e `BMI` (discretizado em categorias de IMC da OMS).
2. **Métricas propostas:** as 5 abaixo, cobrindo os tipos de métrica vistos em aula (contagem, taxa, razão, proporção).
3. **Widgets que controlam o dashboard:** sexo (`st.segmented_control`), faixas etárias (`st.pills`, multisseleção), variável de agrupamento do gráfico de barras (`st.segmented_control`) e o **clique numa barra** do gráfico Altair (`on_select="rerun"`), que filtra os KPIs e o gráfico de IMC.
4. **Rascunho:** `entregas/rascunho-dashboard2.png`.

Todas as métricas são recalculadas a cada mudança de widget ou clique, sobre uma tabela pré-agregada em cache (`@st.cache_data`).

---

## Métrica 1: Pessoas na seleção
- **Variável:** contagem de linhas (pessoas) após os filtros de `sexo_label`, `faixa_etaria` e o clique no gráfico.
- **O que mede:** o tamanho do grupo que está sendo analisado. **Tipo:** contagem.
- **Por que foi escolhida:** dá a escala e a confiabilidade dos demais números; uma prevalência calculada sobre 300 pessoas não tem o mesmo peso que uma sobre 100 mil.
- **Público-alvo:** todos os usuários do painel.
- **Qual decisão pode ser apoiada por essa métrica?** Dimensionar ações (quantas pessoas uma campanha atingiria) e decidir se o recorte é grande o suficiente para tirar conclusões.
- **O que comunica ao público-alvo:** "estes indicadores falam de N pessoas".

## Métrica 2: Prevalência de doença cardíaca
- **Variável:** `Heart_Disease` ("Yes" / "No").
- **O que mede:** % de pessoas da seleção que relatam doença cardíaca, com o **delta em pontos percentuais em relação à base geral** (8,1%). O delta usa `delta_color="inverse"`: subir aparece em vermelho, porque é ruim. **Tipo:** taxa + variação.
- **Por que foi escolhida:** é o desfecho central do dataset; a EDA mostrou que a classe "Yes" é rara (~8%), então a taxa comunica melhor do que a contagem absoluta.
- **Público-alvo:** gestores de saúde pública.
- **Qual decisão pode ser apoiada por essa métrica?** Priorizar grupos para rastreamento cardiovascular (ex.: 65+ tem 15,8%, quase o dobro da média, +7,7 p.p.).
- **O que comunica ao público-alvo:** "neste grupo, X em cada 100 pessoas têm doença cardíaca, Y pontos acima/abaixo da média da população".

## Métrica 3: Risco relativo do fumo
- **Variável:** `Smoking_History` cruzada com `Heart_Disease`.
- **O que mede:** prevalência de doença cardíaca entre quem já fumou ÷ prevalência entre quem nunca fumou, dentro da seleção. **Tipo:** razão (variação relativa).
- **Por que foi escolhida:** traduz a associação entre um fator de risco modificável e o desfecho num único número fácil de ler ("2,1x"), sem exigir tabela de contingência.
- **Público-alvo:** equipes de prevenção e o público leigo.
- **Qual decisão pode ser apoiada por essa métrica?** Direcionar campanhas antitabagismo para os grupos em que a razão é maior.
- **O que comunica ao público-alvo:** "quem já fumou tem cerca de 2 vezes mais doença cardíaca do que quem nunca fumou". Observação: é associação em dados observacionais, não prova de causa.

## Métrica 4: Sedentários
- **Variável:** `Exercise` ("No" = não fez atividade física no último mês).
- **O que mede:** % de pessoas da seleção sem exercício físico. **Tipo:** proporção.
- **Por que foi escolhida:** sedentarismo é um fator de risco cardiovascular modificável e varia bastante entre grupos (22,5% na base, 27,6% entre 65+).
- **Público-alvo:** gestores de programas de atividade física e atenção primária.
- **Qual decisão pode ser apoiada por essa métrica?** Onde investir em programas de incentivo à atividade física.
- **O que comunica ao público-alvo:** "cerca de 1 em cada 4 pessoas deste grupo não se exercita".

## Métrica 5: Obesidade (IMC ≥ 30)
- **Variável:** `BMI`, discretizado nas faixas da OMS (abaixo do peso < 18,5; normal < 25; sobrepeso < 30; obesidade ≥ 30).
- **O que mede:** % de pessoas da seleção com IMC de 30 ou mais. **Tipo:** proporção (variável contínua transformada em categoria).
- **Por que foi escolhida:** o IMC é contínuo e assimétrico (ver Dashboard 1); o corte da OMS é conhecido pelo público e transforma a distribuição numa leitura direta. O gráfico ao lado mostra a prevalência de doença cardíaca em cada categoria de IMC, que sobe de ~6% (normal) para ~10% (obesidade).
- **Público-alvo:** equipes de saúde e público leigo.
- **Qual decisão pode ser apoiada por essa métrica?** Priorizar ações de controle de peso e nutrição para os grupos com maior proporção de obesidade.
- **O que comunica ao público-alvo:** "1 em cada 3 pessoas tem obesidade, e quem tem obesidade tem mais doença cardíaca".
