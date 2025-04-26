import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Property Purchase Comparison", page_icon="🏠", layout="wide"
)

st.title("Comparação de compra de imóvel à vista vs financiado")
st.markdown(
    """
Este aplicativo compara as implicações financeiras de comprar uma propriedade com pagamento à vista 
versus financiando-a. Insira seus parâmetros para ver a comparação.
"""
)

with st.sidebar:
    st.header("Parâmetros de entrada")

    property_value = st.number_input(
        "Valor da propriedade ($)", min_value=10000, value=300000, step=10000
    )

    available_cash = st.number_input(
        "Quantidade de dinheiro disponível agora ($)",
        min_value=0,
        value=100000,
        step=10000,
    )

    initial_monthly_saving = st.number_input(
        "Quantidade de dinheiro que você pode economizar por mês ($)",
        min_value=0,
        value=1000,
        step=100,
    )

    current_rent = st.number_input(
        "Valor do aluguel atual ($)", min_value=0, value=1000, step=100
    )

    monthly_inflation_rate = st.number_input(
        "Taxa de inflação mensal (%)", min_value=0.0, value=0.41, step=0.01
    )

    monthly_investment_return_rate = st.number_input(
        "Taxa de retorno mensal da sua aplicação (%)",
        min_value=0.0,
        value=1.0,
        step=0.01,
    )

    monthly_property_value_increase = st.number_input(
        "Taxa de aumento do valor da propriedade por mês (%)",
        min_value=0.0,
        value=0.8,
        step=0.01,
    )

months_to_simulate = st.number_input("Mês a simular", min_value=1, value=120, step=1)

monthly_savings = [float(initial_monthly_saving)]
months = [1]

for _ in range(months_to_simulate - 1):
    monthly_savings.append(monthly_savings[-1] * (1 + monthly_inflation_rate / 100))
    months.append(months[-1] + 1)

df = pd.DataFrame(
    {
        "month": months,
        "monthly_savings": monthly_savings,
    }
)

fig = px.line(
    df,
    x="month",
    y="monthly_savings",
    title="Quantidade de dinheiro que você deve guardar por mês",
)
st.plotly_chart(fig)


def simulate_property_purchase():
    st.markdown("## A vista")

    savings = [float(available_cash)]
    property_values = [float(property_value)]

    for i in range(months_to_simulate - 1):
        last_saving = savings[-1]
        new_saving = (
            last_saving * (1 + monthly_investment_return_rate / 100)
            + monthly_savings[i]
        )
        savings.append(new_saving)
        last_property_value = property_values[-1]
        new_property_value = last_property_value * (
            1 + monthly_property_value_increase / 100
        )
        property_values.append(new_property_value)

    df = pd.DataFrame(
        {
            "month": months,
            "savings": savings,
            "property_values": property_values,
        }
    )

    fig = px.line(
        df,
        x="month",
        y=["savings", "property_values"],
        title="Saldo e Valor da Propriedade",
    )
    st.plotly_chart(fig)


def simulate_property_purchase_financed():
    st.markdown("## Financiado")

    st.markdown(
        "Estou levando em consideração que você vai pagar todo o valor que você consegue guardar "
        "mensalmente, abatendo parcelas futuras. Também estou considerando que a quantia que você "
        "consegue guardar aumenta com a inflação."
    )

    number_of_installments = st.number_input(
        "Quantidade de parcelas", min_value=1, value=120, step=1
    )

    tax = st.number_input(
        "Taxa de juros mensal (%)", min_value=0.0, value=0.91, step=0.01
    )

    months_to_stop_paying_rent = st.number_input(
        "Quantos meses vai demorar para parar de pagar aluguel?",
        min_value=0,
        value=12,
        step=1,
    )

    first_installment_value = (
        (property_value - available_cash)
        * (tax / 100)
        * (1 + tax / 100) ** number_of_installments
        / ((1 + tax / 100) ** number_of_installments - 1)
    )

    st.write(f"Primeira parcela: R$ {round(first_installment_value, 2)}")

    if first_installment_value > monthly_savings[0]:
        st.warning(
            f"Você não tem dinheiro suficiente para pagar a primeira parcela. Tente aumentar a quantidade de parcelas."
        )
        return

    installment_values = [
        first_installment_value / ((1 + tax / 100) ** i)
        for i in range(1, number_of_installments + 1)
    ]

    need_to_pay = [sum(installment_values)]
    rent = [current_rent]
    what_left_from_last_installment = 0

    for i in range(months_to_simulate - 1):
        corrected_monthly_savings = (
            monthly_savings[i] + what_left_from_last_installment
            if i < months_to_stop_paying_rent
            else monthly_savings[i] + rent[i] + what_left_from_last_installment
        )
        corrected_monthly_savings -= installment_values[i]
        installment_values[i] = 0

        for j in range(len(installment_values) - 1, i - 1, -1):
            if corrected_monthly_savings >= installment_values[j]:
                corrected_monthly_savings -= installment_values[j]
                installment_values[j] = 0

        what_left_from_last_installment = corrected_monthly_savings

        new_need_to_pay = sum(installment_values)
        need_to_pay.append(new_need_to_pay)
        rent.append(rent[-1] * (1 + monthly_inflation_rate / 100))
        if new_need_to_pay == 0:
            break
    df = pd.DataFrame(
        {
            "month": months[: len(need_to_pay)],
            "need_to_pay": need_to_pay,
        }
    )

    fig = px.line(
        df,
        x="month",
        y="need_to_pay",
        title="Quantidade de dinheiro que vai faltar pagar por mês",
    )
    st.plotly_chart(fig)


simulate_property_purchase()
simulate_property_purchase_financed()
