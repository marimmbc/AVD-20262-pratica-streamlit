import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Correlação e distribuição — CVD",
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

df = load_data()


def formatar_numero(n):
    """Formata inteiros no padrão brasileiro (308.611)."""
    return f"{n:,}".replace(",", ".")


def grafico_correlacao(dados, variaveis, metodo):
    """Heatmap da matriz de correlação (calculada no pandas, só 7x7 vai pro Altair)."""
    matriz = dados[variaveis].corr(method=metodo.lower())
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
            legend=alt.Legend(title=f"ρ ({metodo})"),
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


def grafico_distribuicao(dados, variavel, separar):
    """Histograma pré-agregado no numpy (o Altair recebe só as barras, não 300 mil linhas)."""
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
    barras = pd.concat(linhas, ignore_index=True)

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
# [1] Sidebar: filtros (variáveis + classe + intervalo)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")

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

# Mantém só as pessoas dentro de todos os intervalos escolhidos
df_filtrado = df
for var, (inicio, fim) in intervalos.items():
    df_filtrado = df_filtrado[df_filtrado[var].between(inicio, fim)]

# ---------------------------------------------------------------------------
# [2] Topo: título + quantas pessoas sobraram após os filtros
# ---------------------------------------------------------------------------
st.title("Correlação e distribuição — fatores de risco cardiovascular (CVD)")
st.caption(
    f"{formatar_numero(len(df_filtrado))} de {formatar_numero(len(df))} pessoas "
    "dentro dos intervalos escolhidos."
)

# Dashboard 1: correlação à esquerda, distribuição à direita
col_correlacao, col_distribuicao = st.columns([1, 1.5])

# ---------------------------------------------------------------------------
# [3] Correlação
# ---------------------------------------------------------------------------
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
        elif len(df_filtrado) < 3:
            st.warning("Poucas pessoas dentro dos intervalos. Amplie os filtros.")
        else:
            st.altair_chart(
                grafico_correlacao(df_filtrado, variaveis, metodo), width="stretch"
            )
            if df_filtrado[variaveis].nunique().min() < 2:
                st.caption(
                    "Alguma variável ficou com um único valor no intervalo escolhido, "
                    "então a correlação dela não pode ser calculada (célula vazia)."
                )

# ---------------------------------------------------------------------------
# [4] Distribuição
# ---------------------------------------------------------------------------
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

            if df_filtrado.empty:
                st.warning("Ninguém dentro dos intervalos escolhidos. Amplie os filtros.")
            else:
                st.altair_chart(
                    grafico_distribuicao(df_filtrado, var_hist, separar_por_classe),
                    width="stretch",
                )

# TODO (Aula 22/23): Dashboard 2 — KPIs (em st.tabs)