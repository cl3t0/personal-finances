import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import locale

locale.setlocale(locale.LC_MONETARY, "pt_BR.UTF-8")

st.set_page_config(
    page_title="Negócio ou emprego?",
    page_icon="💼",
    layout="wide",
)

st.title("Negócio ou emprego?")
st.markdown(
    """
Este simulador compara a trajetória financeira de continuar em um negócio (com equity) versus trabalhar
como funcionário. Todos os valores monetários devem ser inseridos em **R\$ nominais** — o simulador usa a
inflação para expressar tudo em R\$ de hoje e tornar a comparação justa.
"""
)

with st.sidebar:
    st.header("Parâmetros de entrada")

    st.subheader("Janela de simulação")
    ano_inicio = st.number_input(
        "Ano de início (a partir de hoje)",
        min_value=0,
        max_value=20,
        value=2,
        step=1,
        help="Ano em que a simulação começa, contado a partir de hoje.",
    )
    ano_fim = st.number_input(
        "Ano do evento de liquidez",
        min_value=1,
        max_value=30,
        value=6,
        step=1,
        help="Ano do evento de liquidez (venda, IPO, buyout), contado a partir de hoje.",
    )

    st.subheader("Participação na empresa")
    equity_inicio_pct = st.number_input(
        "Participação no início da janela (%)",
        min_value=0.0,
        max_value=100.0,
        value=10.0,
        step=0.5,
    )
    equity_fim_pct = st.number_input(
        "Participação no evento de liquidez (%)",
        min_value=0.0,
        max_value=100.0,
        value=7.0,
        step=0.5,
        help="Pode ser menor que o início por diluição de rodadas futuras.",
    )

    st.subheader("Alternativa como funcionário")
    remuneracao_mensal = st.number_input(
        "Remuneração total mensal (R$)",
        min_value=0,
        value=20_000,
        step=1_000,
        help=(
            "Inclua tudo: salário, bônus, benefícios, VR/VA, plano de saúde, FGTS, "
            "13º salário, etc. Este é o valor total que você deixaria de receber."
        ),
    )

    st.subheader("Risco")
    probabilidade_sucesso = st.slider(
        "Probabilidade de atingir o evento de liquidez (%)",
        min_value=1,
        max_value=100,
        value=30,
        step=1,
    )

    st.subheader("Receita da empresa")
    receita_inicio = st.number_input(
        "Receita anual no início da janela (R$)",
        min_value=0,
        value=1_000_000,
        step=50_000,
    )
    receita_alvo = st.number_input(
        "Receita anual no evento de liquidez (R$)",
        min_value=0,
        value=5_000_000,
        step=100_000,
    )
    margem_lucro_pct = st.number_input(
        "Margem de lucro líquida (%)",
        min_value=0.0,
        max_value=100.0,
        value=15.0,
        step=1.0,
        help="Percentual do lucro líquido distribuível como dividendos.",
    )

    st.subheader("Valuation")
    valuation_saida = st.number_input(
        "Valuation no evento de liquidez (R$)",
        min_value=0,
        value=20_000_000,
        step=500_000,
    )

    st.subheader("Pró-labore")
    prolabore_inicio = st.number_input(
        "Pró-labore mensal no início da janela (R$)",
        min_value=0,
        value=8_000,
        step=500,
    )
    prolabore_fim = st.number_input(
        "Pró-labore mensal no evento de liquidez (R$)",
        min_value=0,
        value=15_000,
        step=500,
    )

    st.subheader("Inflação")
    inflacao_anual_pct = st.number_input(
        "Taxa de inflação anual (%)",
        min_value=0.0,
        value=4.5,
        step=0.1,
    )

# ── Validation ────────────────────────────────────────────────────────────────
if ano_fim <= ano_inicio:
    st.error("O ano do evento de liquidez deve ser maior que o ano de início.")
    st.stop()

# ── Derived constants ─────────────────────────────────────────────────────────
multiplicador_requerido = 100.0 / probabilidade_sucesso
window_length = ano_fim - ano_inicio
r = inflacao_anual_pct / 100.0
multiple_valuation = valuation_saida / receita_alvo if receita_alvo > 0 else 0.0


def lerp(a, b, t):
    return a + t * (b - a)


def hoje(value, ano):
    """Converte valor nominal do ano `ano` para R$ de hoje."""
    return value / (1 + r) ** ano


# ── Year-by-year simulation ───────────────────────────────────────────────────
sim_years = list(range(ano_inicio, ano_fim + 1))
labels = [f"Ano {y}" for y in sim_years]

emp_cash_yr = []
biz_cash_yr = []
biz_equity_yr = []
detail_rows = []

# Nominal values for contextual charts (no inflation discount)
revenue_yr_nom = []
valuation_yr_nom = []
equity_value_yr_nom = []
prolabore_anual_yr_nom = []
dividendos_yr_nom = []

for i, ano in enumerate(sim_years):
    t = i / window_length

    revenue_t = lerp(receita_inicio, receita_alvo, t)
    equity_t = lerp(equity_inicio_pct, equity_fim_pct, t) / 100.0
    prolabore_t = lerp(prolabore_inicio, prolabore_fim, t)

    # Derived valuation: revenue × constant multiple (fixed at exit ratio)
    valuation_t = revenue_t * multiple_valuation if ano < ano_fim else valuation_saida

    prolabore_anual = prolabore_t * 12.0
    dividendos_t = revenue_t * (margem_lucro_pct / 100.0) * equity_t
    biz_cash_anual = prolabore_anual + dividendos_t

    # Employee: nominal salary grows with inflation so that real value = remuneracao_mensal
    emp_anual_nominal = remuneracao_mensal * 12.0 * (1 + r) ** ano
    emp_cash_yr.append(hoje(emp_anual_nominal, ano))   # = remuneracao_mensal * 12

    biz_cash_yr.append(hoje(biz_cash_anual, ano))
    biz_equity_yr.append(hoje(equity_t * valuation_t, ano))

    revenue_yr_nom.append(revenue_t)
    valuation_yr_nom.append(valuation_t)
    equity_value_yr_nom.append(equity_t * valuation_t)
    prolabore_anual_yr_nom.append(prolabore_anual)
    dividendos_yr_nom.append(dividendos_t)

    detail_rows.append(
        {
            "Ano": ano,
            "Receita anual": revenue_t,
            "Pró-labore mensal": prolabore_t,
            "Dividendos anuais": dividendos_t,
            "Equity (%)": equity_t * 100.0,
            "Valuation": valuation_t,
            "Valor do equity": equity_t * valuation_t,
            "Fluxo negócio (anual)": biz_cash_anual,
            "Fluxo empregado (anual)": emp_anual_nominal,
        }
    )

# ── Accumulated capital (in today's R$) ──────────────────────────────────────
emp_acc = []
biz_cash_acc = []
biz_total_acc = []

running_emp = 0.0
running_biz = 0.0

for i in range(len(sim_years)):
    running_emp += emp_cash_yr[i]
    running_biz += biz_cash_yr[i]
    emp_acc.append(running_emp)
    biz_cash_acc.append(running_biz)
    biz_total_acc.append(running_biz + biz_equity_yr[i])

# ── Summary metrics ───────────────────────────────────────────────────────────
employee_total = emp_acc[-1]
biz_success_total = biz_total_acc[-1]
biz_failure_total = biz_cash_acc[-1]   # no equity in failure scenario

multiplicador_real = biz_success_total / employee_total if employee_total > 0 else 0.0

breakeven_year = None
for i, ano in enumerate(sim_years):
    if biz_total_acc[i] >= emp_acc[i]:
        breakeven_year = ano
        break


def fmt(v):
    """Formata valor para uso em st.metric() (texto simples, sem markdown)."""
    return locale.currency(v, grouping=True)


# ── Metrics display ───────────────────────────────────────────────────────────
st.subheader("Resumo no evento de liquidez (valores em R\\$ de hoje)")

c1, c2, c3 = st.columns(3)
c1.metric("Capital acumulado — Empregado", fmt(employee_total))
c2.metric("Capital acumulado — Negócio (sucesso)", fmt(biz_success_total))
c3.metric("Capital acumulado — Negócio (fracasso)", fmt(biz_failure_total))

c4, c5, c6 = st.columns(3)
c4.metric(
    "Multiplicador real (sucesso ÷ empregado)",
    f"{multiplicador_real:.2f}x",
    delta=f"{multiplicador_real - multiplicador_requerido:+.2f}x vs requerido",
)
c5.metric(
    "Multiplicador mínimo requerido (1 ÷ prob. sucesso)",
    f"{multiplicador_requerido:.2f}x",
)
c6.metric(
    "Break-even",
    f"Ano {breakeven_year}" if breakeven_year else "Não atingido",
    help="Primeiro ano em que o capital total do negócio supera o do empregado.",
)

# ── Chart 1: company & equity growth ─────────────────────────────────────────
st.subheader("A empresa e o seu equity")
st.caption("Evolução nominal da receita, do valuation e do valor do seu equity ao longo do tempo.")

fig_empresa = go.Figure()

fig_empresa.add_trace(go.Scatter(
    name="Receita anual",
    x=labels,
    y=revenue_yr_nom,
    mode="lines+markers",
    line=dict(color="#2196F3", width=2),
))
fig_empresa.add_trace(go.Scatter(
    name="Valuation da empresa",
    x=labels,
    y=valuation_yr_nom,
    mode="lines+markers",
    line=dict(color="#4CAF50", width=2),
))
fig_empresa.add_trace(go.Scatter(
    name="Valor do seu equity",
    x=labels,
    y=equity_value_yr_nom,
    mode="lines+markers",
    line=dict(color="#FF9800", width=2),
    fill="tozeroy",
    fillcolor="rgba(255, 152, 0, 0.1)",
))

fig_empresa.update_layout(
    xaxis_title="Ano (a partir de hoje)",
    yaxis_title="Valor (R$ nominal)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400,
)

st.plotly_chart(fig_empresa, use_container_width=True)

# ── Chart 2: annual cash flows ────────────────────────────────────────────────
st.subheader("Fluxo de caixa anual")
st.caption(
    "Quanto você recebe por ano em cada cenário (valores nominais). "
    "A linha tracejada é a remuneração anual como funcionário em R\\$ de hoje."
)

emp_salario_anual_ref = remuneracao_mensal * 12

fig_fluxo = go.Figure()

fig_fluxo.add_trace(go.Bar(
    name="Pró-labore",
    x=labels,
    y=prolabore_anual_yr_nom,
    marker_color="#4CAF50",
))
fig_fluxo.add_trace(go.Bar(
    name="Dividendos",
    x=labels,
    y=dividendos_yr_nom,
    marker_color="#8BC34A",
))
fig_fluxo.add_trace(go.Scatter(
    name="Remuneração como funcionário",
    x=labels,
    y=[emp_salario_anual_ref] * len(labels),
    mode="lines",
    line=dict(color="#2196F3", width=2, dash="dash"),
))

fig_fluxo.update_layout(
    barmode="stack",
    xaxis_title="Ano (a partir de hoje)",
    yaxis_title="Fluxo de caixa anual (R$ nominal)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400,
)

st.plotly_chart(fig_fluxo, use_container_width=True)

# ── Capital chart ─────────────────────────────────────────────────────────────
st.subheader("Capital acumulado por ano")
st.caption(
    "Valores em R\\$ de hoje (descontados pela inflação). "
    "O equity é mostrado em papel até o evento de liquidez, quando se torna caixa."
)

fig = go.Figure()

fig.add_trace(
    go.Bar(
        name="Empregado",
        x=labels,
        y=emp_acc,
        marker_color="#2196F3",
        offsetgroup=0,
    )
)

fig.add_trace(
    go.Bar(
        name="Negócio — Caixa (pró-labore + dividendos)",
        x=labels,
        y=biz_cash_acc,
        marker_color="#4CAF50",
        offsetgroup=1,
    )
)

fig.add_trace(
    go.Bar(
        name="Negócio — Equity (papel)",
        x=labels,
        y=biz_equity_yr,
        base=biz_cash_acc,
        marker_color="#FF9800",
        marker_opacity=0.75,
        offsetgroup=1,
    )
)

fig.update_layout(
    barmode="group",
    xaxis_title="Ano (a partir de hoje)",
    yaxis_title="Capital acumulado (R$ de hoje)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=480,
)

st.plotly_chart(fig, use_container_width=True)

# ── Valuation multiple info ───────────────────────────────────────────────────
if receita_alvo > 0:
    st.info(
        f"Múltiplo de valuation implícito: **{multiple_valuation:.1f}x receita** — "
        "o valuation dos anos intermediários é derivado da receita multiplicada por esse valor."
    )

# ── Intermediate calculations table ──────────────────────────────────────────
st.subheader("Detalhamento anual (valores nominais)")

df = pd.DataFrame(detail_rows).set_index("Ano")

currency_cols = [
    "Receita anual",
    "Pró-labore mensal",
    "Dividendos anuais",
    "Valuation",
    "Valor do equity",
    "Fluxo negócio (anual)",
    "Fluxo empregado (anual)",
]
for col in currency_cols:
    df[col] = df[col].apply(lambda v: locale.currency(v, grouping=True))

df["Equity (%)"] = df["Equity (%)"].apply(lambda v: f"{v:.2f}%")

st.dataframe(df, use_container_width=True)

# ── Verdict ───────────────────────────────────────────────────────────────────
st.subheader("Veredicto")

if multiplicador_real >= multiplicador_requerido:
    st.success(
        f"Vale a pena ficar no negócio. "
        f"No cenário de sucesso o negócio gera **{multiplicador_real:.2f}x** o capital do emprego, "
        f"superior ao mínimo requerido de {multiplicador_requerido:.2f}x "
        f"(dado {probabilidade_sucesso}% de probabilidade de sucesso)."
        + (
            f" O negócio supera o emprego já no **ano {breakeven_year}**."
            if breakeven_year and breakeven_year < ano_fim
            else ""
        )
    )
else:
    st.warning(
        f"O negócio pode não compensar. "
        f"No cenário de sucesso o negócio gera apenas **{multiplicador_real:.2f}x** o capital do emprego, "
        f"abaixo do mínimo requerido de {multiplicador_requerido:.2f}x "
        f"(dado {probabilidade_sucesso}% de probabilidade de sucesso). "
        f"Para mudar o veredicto, revise o valuation de saída, a receita alvo, o pró-labore ou a probabilidade de sucesso."
    )
