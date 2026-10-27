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

df = load_data()


def formatar_numero(n):
    """Formata inteiros no padrão brasileiro (308.611)."""
    return f"{n:,}".replace(",", ".")


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
        else:
            # TODO (Aula 22): matriz = df_filtrado[variaveis].corr(method=metodo.lower())
            # TODO (Aula 22): heatmap com plotly (px.imshow) e exibir com st.plotly_chart
            st.info(f"Heatmap da correlação de {metodo} entra aqui.", icon=":material/grid_on:")

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

            # TODO (Aula 22): histograma com plotly (px.histogram) de df_filtrado[var_hist]
            #       se separar_por_classe: color=CLASSE
            #       exibir com st.plotly_chart
            legenda = f", separado por {CLASSE}" if separar_por_classe else ""
            st.info(f"Histograma de {var_hist}{legenda} entra aqui.", icon=":material/bar_chart:")

# TODO (Aula 22): Dashboard 2 — KPIs