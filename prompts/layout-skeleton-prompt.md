# Template: rascunho de layout → esqueleto do app

## Contexto

Sou aluna de Ciência da Computação na Cesar School, na disciplina Análise e Visualização de Dados (2026.2). Estou construindo dashboards em Streamlit a partir da EDA que fiz na Aula 11.

O dataset é o Cardiovascular Diseases Risk Prediction (CVD), com cerca de 308 mil pessoas, já tratado no notebook `notebooks/eda.ipynb` e exportado para `data/clean/dataset.csv`.

Este é o Dashboard 1, cujo objetivo é analisar a **correlação** e a **distribuição** das variáveis quantitativas, permitindo filtrar intervalos para ver se a remoção de valores extremos muda os resultados.

Estrutura do repositório:
- `app.py`: app Streamlit (arquivo a ser gerado)
- `src/data_loader.py`: função `load_data()` que lê `data/clean/dataset.csv`
- `data/clean/dataset.csv`: dataset tratado
- `notebooks/eda.ipynb`: EDA
- `prompts/`: rascunhos e prompts

## Entrada

Rascunho do layout em anexo: `prompts/rascunho_dashboard1.png`.

Layout:
- Sidebar à esquerda com o título "Filtros":
  - `st.multiselect` com as variáveis quantitativas (todas selecionadas por padrão)
  - `st.toggle` "Distinguir por Heart_Disease"
  - um `st.slider` de intervalo para cada variável selecionada
- Área principal:
  - título no topo e um `st.caption` com quantas pessoas estão dentro dos intervalos
  - duas colunas (`st.columns([1, 1.5])`): à esquerda "Correlação", à direita "Distribuição"
  - Correlação: `st.radio` para escolher Pearson ou Spearman (Spearman como padrão) e espaço para o heatmap
  - Distribuição: `st.selectbox` para escolher uma das variáveis selecionadas e espaço para o histograma

Variáveis quantitativas: `Height_(cm)`, `Weight_(kg)`, `BMI`, `Alcohol_Consumption`, `Fruit_Consumption`, `Green_Vegetables_Consumption`, `FriedPotato_Consumption`.

Variável de classe: `Heart_Disease` (valores "No" e "Yes").

Perguntas que o dashboard deve responder:
- Quais variáveis quantitativas são mais correlacionadas entre si?
- Como cada variável se distribui, e essa distribuição muda entre quem tem e quem não tem doença cardíaca?
- Remover valores extremos altera a correlação ou a distribuição?

## Restrições

- Usar Streamlit; os gráficos (próxima aula) serão feitos com plotly.
- Editar apenas o `app.py`; carregar os dados com `from src.data_loader import load_data`.
- Gerar só o esqueleto estrutural: widgets e containers funcionando, filtragem do dataframe pelos sliders, mas **sem gerar os gráficos**.
- Nos espaços dos gráficos, usar placeholders (`st.info` ou comentários `# TODO`).
- Se menos de 2 variáveis forem selecionadas, mostrar `st.warning` no bloco de Correlação.
- Não usar CSS customizado nem `unsafe_allow_html`.
- Seguir as boas práticas das skills do Streamlit instaladas no projeto.

## Formato de saída

- Um único `app.py` completo, pronto para `streamlit run app.py`.
- Comentários curtos separando cada seção (sidebar, topo, correlação, distribuição).
- `# TODO` nos pontos onde os gráficos serão adicionados na próxima aula.
- Uma explicação breve (poucas linhas) de cada seção depois do código.