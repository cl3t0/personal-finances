import streamlit as st
import locale
import pandas as pd
import plotly.express as px

locale.setlocale(locale.LC_MONETARY, "pt_BR.UTF-8")

with st.sidebar:
    current_capital = st.number_input("Capital atual (R$)", value=0, step=1000)
    monthly_inflation_rate = st.number_input(
        "Taxa de inflação mensal (%)", min_value=0.0, value=0.41, step=0.01
    )

    monthly_investment_return_rate = st.number_input(
        "Taxa de retorno mensal da sua aplicação (%)",
        min_value=0.0,
        value=1.0,
        step=0.01,
    )


def calculate_monthly_savings(
    wanted_buy_power: float,
    time_to_retire: float,
    current_capital: float,
    monthly_inflation_rate: float,
    monthly_investment_return_rate: float,
) -> tuple[float, float]:
    months_to_retire = time_to_retire * 12
    salary_at_retire = (
        wanted_buy_power * (1 + monthly_inflation_rate / 100) ** months_to_retire
    )

    total_amount = salary_at_retire / (
        monthly_investment_return_rate / 100 - monthly_inflation_rate / 100
    )

    monthly_savings = (
        monthly_investment_return_rate
        / 100
        * (
            total_amount
            - current_capital
            * (1 + monthly_investment_return_rate / 100) ** months_to_retire
        )
        / ((1 + monthly_investment_return_rate / 100) ** months_to_retire - 1)
    )
    return monthly_savings, salary_at_retire


points = [
    (
        wanted_buy_power,
        time_to_retire,
        *calculate_monthly_savings(
            wanted_buy_power,
            time_to_retire,
            current_capital,
            monthly_inflation_rate,
            monthly_investment_return_rate,
        ),
    )
    for wanted_buy_power in range(1000, 50000, 1000)
    for time_to_retire in range(5, 30, 5)
]


df = pd.DataFrame(
    {
        "wanted_buy_power": [round(p[0], 2) for p in points],
        "time_to_retire": [p[1] for p in points],
        "monthly_savings": [round(p[2], 2) for p in points],
        "future_salary": [round(p[3], 2) for p in points],
    }
)

fig = px.line(
    df,
    y="wanted_buy_power",
    x="monthly_savings",
    color="time_to_retire",
    title="Poupança mensal necessária para se aposentar com diferentes salários desejados e tempos para aposentar",
    labels={
        "wanted_buy_power": "Poder de compra desejado (R$)",
        "monthly_savings": "Poupança mensal necessária (R$)",
        "time_to_retire": "Anos para aposentar",
        "future_salary": "Salário ao aposentar (R$)",
    },
    hover_data=["future_salary"],
)
st.plotly_chart(fig)

st.title("Cálculo com valores específicos")

wanted_buy_power = st.number_input(
    "Poder de compra desejado (R$)", value=10000, step=1000
)
time_to_retire = st.number_input("Anos para aposentar", value=20, step=1)
monthly_savings, future_salary = calculate_monthly_savings(
    wanted_buy_power,
    time_to_retire,
    current_capital,
    monthly_inflation_rate,
    monthly_investment_return_rate,
)

st.write(
    f"Poupança mensal necessária: {locale.currency(monthly_savings, grouping=True)}"
)
st.write(f"Salário ao aposentar: {locale.currency(future_salary, grouping=True)}")
