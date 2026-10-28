import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Fatores de risco cardiovascular — CVD",
    page_icon=":material/cardiology:",
    layout="wide",
)

# Variáveis quantitativas do estudo (mesma lista VARS_QUANT do notebook de EDA)
VARS_QUANT = [
    "Height_(cm)",
    "Weight_(kg)",
    "BMI",
    "Alcohol_Consumption",
    "Fruit_Consumption",
    "Green_Vegetables_Consumption",
    "FriedPotato_Consumption",
]
CLASSE = "Heart_Disease"  # "No" / "Yes"

# Mesmas cores da EDA: rosa = "No" (referência), roxo = "Yes" (classe de interesse)
COR_CONTEXTO = "#e9d4d0"
COR_DESTAQUE = "#2d223a"
if st.context.theme.type == "dark":
    # No tema escuro o roxo some no fundo: inverte a luminosidade mantendo a paleta
    COR_CONTEXTO, COR_DESTAQUE = "#5a4766", "#e9b8c8"

# Nomes curtos para os eixos do heatmap (mesmos ROTULOS_CORR da EDA)
ROTULOS = {
    "Height_(cm)": "Height",
    "Weight_(kg)": "Weight",
    "BMI": "BMI",
    "Alcohol_Consumption": "Alcohol",
    "Fruit_Consumption": "Fruit",
    "Green_Vegetables_Consumption": "GreenVeg",
    "FriedPotato_Consumption": "FriedPotato",
}

# Dashboard 2: variáveis categóricas que agrupam os KPIs, com a ordem natural das categorias
FAIXAS_ETARIAS = ["<45", "45-54", "55-64", "65+"]
CATEGORIAS_IMC = ["Abaixo do peso", "Normal", "Sobrepeso", "Obesidade"]
AGRUPAMENTOS = {
    "Faixa etária": ("faixa_etaria", FAIXAS_ETARIAS),
    "Saúde geral": ("General_Health", ["Poor", "Fair", "Good", "Very Good", "Excellent"]),
    "Exercício": ("Exercise", ["Yes", "No"]),
    "Fumante": ("Smoking_History", ["No", "Yes"]),
}

df = load_data()


def formatar_numero(n):
    """Formata inteiros no padrão brasileiro (308.611)."""
    return f"{n:,}".replace(",", ".")


def formatar_percentual(p, casas=1):
    """Formata proporções no padrão brasileiro (8,1%)."""
    return f"{p:.{casas}%}".replace(".", ",")


# ---------------------------------------------------------------------------
# Dashboard 1: cálculos em cache (chave = combinação de widgets)
# ---------------------------------------------------------------------------
def aplicar_intervalos(dados, intervalos):
    """Mantém só as pessoas dentro de todos os intervalos escolhidos."""
    for var, (inicio, fim) in intervalos:
        dados = dados[dados[var].between(inicio, fim)]
    return dados


@st.cache_data(max_entries=100)
def contar_filtrados(intervalos):
    return len(aplicar_intervalos(load_data(), intervalos))


@st.cache_data(max_entries=100)
def calcular_correlacao(intervalos, variaveis, metodo):
    """Matriz de correlação (só 7x7 vai pro Altair, não 300 mil linhas)."""
    dados = aplicar_intervalos(load_data(), intervalos)
    return dados[list(variaveis)].corr(method=metodo.lower())


@st.cache_data(max_entries=100)
def calcular_histograma(intervalos, variavel, separar):
    """Histograma pré-agregado no numpy (o Altair recebe só as barras)."""
    dados = aplicar_intervalos(load_data(), intervalos)
    serie = dados[variavel]
    discreta = variavel.endswith("_Consumption")
    if discreta:
        # Consumos são contagens inteiras: uma barra por valor (até 60 barras)
        largura = max(1.0, np.ceil((serie.max() - serie.min() + 1) / 60))
    else:
        largura = (serie.max() - serie.min()) / 40 or 1.0
    bordas = np.arange(serie.min(), serie.max() + largura, largura)

    grupos = [("Todos", dados)]
    if separar:
        grupos = [(classe, dados[dados[CLASSE] == classe]) for classe in ["No", "Yes"]]

    linhas = []
    for nome, sub in grupos:
        contagem, _ = np.histogram(sub[variavel], bins=bordas)
        total = max(len(sub), 1)
        linhas.append(
            pd.DataFrame(
                {
                    "inicio": bordas[:-1],
                    "fim": bordas[1:],
                    "pessoas": contagem,
                    "percentual": contagem / total,
                    "grupo": nome,
                }
            )
        )
    return pd.concat(linhas, ignore_index=True)


def grafico_correlacao(matriz, metodo):
    """Heatmap da matriz de correlação."""
    matriz = matriz.rename(index=ROTULOS, columns=ROTULOS)
    ordem = list(matriz.columns)
    longo = matriz.reset_index(names="var_x").melt(
        id_vars="var_x", var_name="var_y", value_name="correlacao"
    )

    base = alt.Chart(longo).encode(
        x=alt.X("var_x:N", sort=ordem, title=None, axis=alt.Axis(labelAngle=-45, labelOverlap=False)),
        y=alt.Y("var_y:N", sort=ordem, title=None, axis=alt.Axis(labelOverlap=False)),
    )
    celulas = base.mark_rect().encode(
        color=alt.Color(
            "correlacao:Q",
            scale=alt.Scale(scheme="redblue", domain=[-1, 1], reverse=True),
            legend=alt.Legend(title=f"ρ ({metodo})", orient="bottom", gradientLength=220),
        ),
        tooltip=[
            alt.Tooltip("var_x:N", title="Variável 1"),
            alt.Tooltip("var_y:N", title="Variável 2"),
            alt.Tooltip("correlacao:Q", title="Correlação", format=".2f"),
        ],
    )
    textos = base.mark_text(fontSize=11).encode(
        text=alt.Text("correlacao:Q", format=".2f"),
        color=alt.condition(
            "abs(datum.correlacao) > 0.5", alt.value("white"), alt.value("black")
        ),
    )
    return (celulas + textos).properties(width="container", height=380)


def grafico_distribuicao(barras, variavel, separar):
    """Histograma a partir das barras já calculadas."""
    # Separado por classe, mostra % dentro de cada grupo: "Yes" é só ~8% da base
    # e sumiria numa contagem absoluta
    if separar:
        y = alt.Y("percentual:Q", title="% dentro do grupo", stack=None, axis=alt.Axis(format="%"))
        cor = alt.Color(
            "grupo:N",
            title=CLASSE,
            scale=alt.Scale(domain=["No", "Yes"], range=[COR_CONTEXTO, COR_DESTAQUE]),
        )
        # "Yes" semitransparente por cima, para o "No" aparecer por trás
        opacidade = alt.condition(alt.datum.grupo == "Yes", alt.value(0.6), alt.value(1))
    else:
        y = alt.Y("pessoas:Q", title="Pessoas")
        cor = alt.value(COR_DESTAQUE)
        opacidade = alt.value(1)

    return (
        alt.Chart(barras)
        .mark_bar(binSpacing=1)
        .encode(
            x=alt.X("inicio:Q", bin="binned", title=variavel),
            x2="fim:Q",
            y=y,
            color=cor,
            opacity=opacidade,
            tooltip=[
                alt.Tooltip("grupo:N", title="Grupo"),
                alt.Tooltip("inicio:Q", title="De", format=".1f"),
                alt.Tooltip("fim:Q", title="Até", format=".1f"),
                alt.Tooltip("pessoas:Q", title="Pessoas", format=","),
                alt.Tooltip("percentual:Q", title="% do grupo", format=".1%"),
            ],
        )
        .properties(width="container", height=380)
    )


# ---------------------------------------------------------------------------
# Dashboard 2: agregação em cache (o Altair e os KPIs recebem só ~80 linhas)
# ---------------------------------------------------------------------------
@st.cache_data(max_entries=100)
def agregar_kpis(sexo, faixas, coluna_grupo):
    """Conta pessoas e casos de doença cardíaca por grupo x IMC x fumo x exercício."""
    dados = load_data()
    if sexo != "Todos":
        dados = dados[dados["sexo_label"] == sexo]
    dados = dados[dados["faixa_etaria"].isin(faixas)]

    tabela = pd.DataFrame(
        {
            "grupo": dados[coluna_grupo],
            "imc_categoria": pd.cut(
                dados["BMI"], [0, 18.5, 25, 30, np.inf], right=False, labels=CATEGORIAS_IMC
            ).astype(str),
            "fumante": dados["Smoking_History"],
            "exercicio": dados["Exercise"],
            "doentes": (dados[CLASSE] == "Yes").astype(int),
        }
    )
    return (
        tabela.groupby(["grupo", "imc_categoria", "fumante", "exercicio"], observed=True)
        .agg(pessoas=("doentes", "size"), doentes=("doentes", "sum"))
        .reset_index()
    )


def prevalencia(tabela):
    """Casos / pessoas; NaN quando não há ninguém."""
    pessoas = tabela["pessoas"].sum()
    return tabela["doentes"].sum() / pessoas if pessoas else np.nan


def prevalencia_por(tabela, coluna):
    resumo = tabela.groupby(coluna, as_index=False)[["pessoas", "doentes"]].sum()
    resumo["prevalencia"] = resumo["doentes"] / resumo["pessoas"]
    return resumo


def grafico_prevalencia(resumo, coluna, ordem, titulo_x, selecao=None):
    """Barras de prevalência de doença cardíaca por categoria."""
    barras = alt.Chart(resumo).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    if selecao is not None:
        cor = alt.condition(selecao, alt.value(COR_DESTAQUE), alt.value(COR_CONTEXTO))
        barras = barras.add_params(selecao)
    else:
        cor = alt.value(COR_DESTAQUE)

    eixo_x = alt.X(f"{coluna}:N", sort=ordem, title=titulo_x, axis=alt.Axis(labelAngle=0))
    eixo_y = alt.Y("prevalencia:Q", title="Prevalência de doença cardíaca", axis=alt.Axis(format="%"))
    barras = barras.encode(
        x=eixo_x,
        y=eixo_y,
        color=cor,
        tooltip=[
            alt.Tooltip(f"{coluna}:N", title=titulo_x),
            alt.Tooltip("pessoas:Q", title="Pessoas", format=","),
            alt.Tooltip("doentes:Q", title="Com doença cardíaca", format=","),
            alt.Tooltip("prevalencia:Q", title="Prevalência", format=".1%"),
        ],
    )
    rotulos = (
        alt.Chart(resumo)
        .mark_text(dy=-8, fontSize=12)
        .encode(x=eixo_x, y=eixo_y, text=alt.Text("prevalencia:Q", format=".1%"))
    )
    return (barras + rotulos).properties(width="container", height=340)


# ---------------------------------------------------------------------------
# [1] Sidebar: filtros do Dashboard 1 (variáveis + classe + intervalo)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros do Dashboard 1")

    variaveis = st.multiselect(
        "Variáveis quantitativas",
        options=VARS_QUANT,
        default=VARS_QUANT,
        help="Variáveis que entram na correlação e na distribuição.",
    )

    separar_por_classe = st.toggle(
        f"Distinguir por {CLASSE}",
        value=False,
        help="Colore a distribuição por presença de doença cardíaca (No / Yes).",
    )

    st.subheader("Intervalo de cada variável")
    st.caption("Remova valores extremos e veja se a correlação ou a distribuição muda.")

    # Um slider de intervalo para cada variável selecionada
    intervalos = {}
    for var in variaveis:
        minimo, maximo = float(df[var].min()), float(df[var].max())
        # Consumos são contagens inteiras; altura, peso e BMI são contínuos
        passo = 1.0 if var.endswith("_Consumption") else 0.1
        intervalos[var] = st.slider(
            var,
            min_value=minimo,
            max_value=maximo,
            value=(minimo, maximo),
            step=passo,
            key=f"intervalo_{var}",
        )

# Tupla (hashable) para servir de chave do cache
intervalos_chave = tuple(intervalos.items())
n_filtrados = contar_filtrados(intervalos_chave)

st.title("Fatores de risco cardiovascular (CVD)")

aba_d1, aba_d2 = st.tabs(
    [":material/scatter_plot: Correlação e distribuição", ":material/monitoring: Indicadores (KPIs)"]
)

# ===========================================================================
# Dashboard 1 — correlação + distribuição
# ===========================================================================
with aba_d1:
    st.caption(
        f"{formatar_numero(n_filtrados)} de {formatar_numero(len(df))} pessoas "
        "dentro dos intervalos escolhidos na barra lateral."
    )

    col_correlacao, col_distribuicao = st.columns([1, 1.2])

    # -----------------------------------------------------------------------
    # [3] Correlação
    # -----------------------------------------------------------------------
    with col_correlacao:
        with st.container(border=True):
            st.subheader("Correlação")

            metodo = st.segmented_control(
                "Método",
                options=["Pearson", "Spearman"],
                default="Spearman",
                help="Spearman é o padrão porque as variáveis são assimétricas (ver EDA).",
            )
            metodo = metodo or "Spearman"  # se o usuário desmarcar, volta ao padrão

            if len(variaveis) < 2:
                st.warning("Selecione pelo menos 2 variáveis para calcular a correlação.")
            elif n_filtrados < 3:
                st.warning("Poucas pessoas dentro dos intervalos. Amplie os filtros.")
            else:
                matriz = calcular_correlacao(intervalos_chave, tuple(variaveis), metodo)
                st.altair_chart(grafico_correlacao(matriz, metodo), width="stretch")
                if matriz.isna().to_numpy().any():
                    st.caption(
                        "Alguma variável ficou com um único valor no intervalo escolhido, "
                        "então a correlação dela não pode ser calculada (célula vazia)."
                    )

    # -----------------------------------------------------------------------
    # [4] Distribuição
    # -----------------------------------------------------------------------
    with col_distribuicao:
        with st.container(border=True):
            st.subheader("Distribuição")

            if not variaveis:
                st.warning("Selecione pelo menos 1 variável na barra lateral.")
            else:
                var_hist = st.selectbox(
                    "Variável",
                    options=variaveis,
                    index=variaveis.index("BMI") if "BMI" in variaveis else 0,
                )

                if n_filtrados == 0:
                    st.warning("Ninguém dentro dos intervalos escolhidos. Amplie os filtros.")
                else:
                    barras = calcular_histograma(intervalos_chave, var_hist, separar_por_classe)
                    st.altair_chart(
                        grafico_distribuicao(barras, var_hist, separar_por_classe),
                        width="stretch",
                    )

# ===========================================================================
# Dashboard 2 — KPIs de doença cardíaca
# ===========================================================================
with aba_d2:
    # -----------------------------------------------------------------------
    # [5] Widgets do Dashboard 2 (independentes da sidebar)
    # -----------------------------------------------------------------------
    with st.container(horizontal=True, vertical_alignment="bottom"):
        sexo = st.segmented_control(
            "Sexo",
            options=["Todos", "Feminino", "Masculino"],
            default="Todos",
            key="d2_sexo",
        )
        faixas = st.pills(
            "Faixa etária",
            options=FAIXAS_ETARIAS,
            selection_mode="multi",
            default=FAIXAS_ETARIAS,
            key="d2_faixas",
        )
        nome_grupo = st.segmented_control(
            "Agrupar por",
            options=list(AGRUPAMENTOS),
            default="Faixa etária",
            key="d2_grupo",
        )
    sexo = sexo or "Todos"
    nome_grupo = nome_grupo or "Faixa etária"
    coluna_grupo, ordem_grupo = AGRUPAMENTOS[nome_grupo]
    # Mantém a ordem natural das faixas, independente da ordem dos cliques
    faixas = tuple(f for f in FAIXAS_ETARIAS if f in (faixas or []))

    if not faixas:
        st.warning("Selecione pelo menos 1 faixa etária.")
        st.stop()

    tabela = agregar_kpis(sexo, faixas, coluna_grupo)
    referencia = prevalencia(agregar_kpis("Todos", tuple(FAIXAS_ETARIAS), coluna_grupo))

    if tabela.empty:
        st.warning("Ninguém com essa combinação de filtros.")
        st.stop()

    # -----------------------------------------------------------------------
    # [7] Visual principal: clique numa barra filtra KPIs e o outro gráfico
    # (desenhado antes dos KPIs no código porque o clique precisa ser lido antes)
    # -----------------------------------------------------------------------
    linha_kpis = st.container()
    col_grupo, col_imc = st.columns(2)

    with col_grupo:
        with st.container(border=True):
            st.subheader(f"Prevalência por {nome_grupo.lower()}")
            st.caption("Clique numa barra para filtrar os indicadores (shift + clique para várias).")
            clique = alt.selection_point(name="clique", fields=["grupo"])
            evento = st.altair_chart(
                grafico_prevalencia(
                    prevalencia_por(tabela, "grupo"), "grupo", ordem_grupo, nome_grupo, clique
                ),
                on_select="rerun",
                key=f"d2_barras_{coluna_grupo}",  # muda a chave para limpar a seleção ao trocar o agrupamento
                width="stretch",
            )

    selecionados = [item["grupo"] for item in evento.selection.get("clique", [])]
    selecao = tabela[tabela["grupo"].isin(selecionados)] if selecionados else tabela
    descricao_selecao = f"{nome_grupo}: {', '.join(selecionados)}" if selecionados else "Toda a seleção"

    with col_imc:
        with st.container(border=True):
            st.subheader("Prevalência por categoria de IMC")
            st.caption(descricao_selecao)
            st.altair_chart(
                grafico_prevalencia(
                    prevalencia_por(selecao, "imc_categoria"),
                    "imc_categoria",
                    CATEGORIAS_IMC,
                    "Categoria de IMC",
                ),
                width="stretch",
            )

    # -----------------------------------------------------------------------
    # [6] KPIs (st.metric) — recalculados com filtros + clique
    # -----------------------------------------------------------------------
    pessoas = int(selecao["pessoas"].sum())
    prev = prevalencia(selecao)
    prev_fumantes = prevalencia(selecao[selecao["fumante"] == "Yes"])
    prev_nao_fumantes = prevalencia(selecao[selecao["fumante"] == "No"])
    razao_fumo = prev_fumantes / prev_nao_fumantes if prev_nao_fumantes else np.nan
    inativos = selecao.loc[selecao["exercicio"] == "No", "pessoas"].sum() / pessoas
    obesos = selecao.loc[selecao["imc_categoria"] == "Obesidade", "pessoas"].sum() / pessoas

    with linha_kpis:
        st.caption(f"Indicadores de: **{descricao_selecao}** · sexo: {sexo} · faixas: {', '.join(faixas)}")
        # Linha que quebra em telas estreitas; altura fixa porque só um KPI tem delta
        estilo_cartao = {"border": True, "height": 140, "width": 195}
        with st.container(horizontal=True):
            st.metric(
                "Pessoas",
                formatar_numero(pessoas),
                help="Quantas pessoas respondem aos filtros e ao clique no gráfico.",
                **estilo_cartao,
            )
            diferenca = round((prev - referencia) * 100, 1)
            st.metric(
                "Doença cardíaca",
                formatar_percentual(prev),
                # Delta 0 numérico fica cinza e sem seta; string "+0,0" ganharia seta verde
                delta=f"{diferenca:+.1f}".replace(".", ",") + " p.p." if diferenca else 0,
                delta_description="vs. base geral",
                delta_color="inverse",  # subir é ruim
                help=(
                    "% de pessoas com doença cardíaca. Base geral: "
                    f"{formatar_percentual(referencia)} das {formatar_numero(len(df))} pessoas."
                ),
                **estilo_cartao,
            )
            st.metric(
                "Risco do fumo",
                "—" if np.isnan(razao_fumo) else f"{razao_fumo:.1f}x".replace(".", ","),
                help="Prevalência entre quem já fumou ÷ prevalência entre quem nunca fumou.",
                **estilo_cartao,
            )
            st.metric(
                "Sedentários",
                formatar_percentual(inativos),
                help="% de pessoas que não fizeram exercício físico no último mês.",
                **estilo_cartao,
            )
            st.metric(
                "Obesidade",
                formatar_percentual(obesos),
                help="% de pessoas com índice de massa corporal (IMC) de 30 ou mais.",
                **estilo_cartao,
            )
