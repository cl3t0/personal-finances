import streamlit as st
import locale
import pandas as pd
import plotly.express as px

locale.setlocale(locale.LC_MONETARY, "pt_BR.UTF-8")

with st.sidebar:
    st.write("Essa simulação não considera capital inicial.")
    monthly_inflation_rate = st.number_input(
        "Taxa de inflação mensal (%)", min_value=0.0, value=0.41, step=0.01
    )

    monthly_investment_return_rate = st.number_input(
        "Taxa de retorno mensal da sua aplicação (%)",
        min_value=0.0,
        value=1.0,
        step=0.01,
    )
    consider_increasing_monthly_savings = st.checkbox(
        "Considerar aumento da poupança mensal acompanhando a inflação?", value=False
    )


def calculate_monthly_savings_rate(
    months_to_retire: int,
    monthly_inflation_rate: float,
    monthly_investment_return_rate: float,
) -> float:
    m = months_to_retire
    r = monthly_investment_return_rate / 100
    i = monthly_inflation_rate / 100

    factor = (
        ((1 + r) ** (m + 1) - (1 + i) ** (m + 1)) / (r - i)
        if consider_increasing_monthly_savings
        else ((1 + r) ** m - 1) / r
    )
    return (1 + i) ** m / (r - i) / factor


points = []
for months_to_retire in range(50 * 12, 0, -1):
    rate = calculate_monthly_savings_rate(
        months_to_retire, monthly_inflation_rate, monthly_investment_return_rate
    )
    if rate > 1:
        break
    points.append((months_to_retire, rate))

df = pd.DataFrame(
    {
        "years_to_retire": [round(p[0] / 12, 2) for p in points],
        "monthly_savings_rate": [round(p[1] * 100, 2) for p in points],
    }
)

fig = px.line(
    df,
    y="years_to_retire",
    x="monthly_savings_rate",
    title="Quantos anos para você se aposentar?",
    labels={
        "years_to_retire": "Anos para aposentar",
        "monthly_savings_rate": "Taxa de poupança mensal necessária para se aposentar (%)",
    },
)
st.plotly_chart(fig)
