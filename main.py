import streamlit as st
import pandas as pd
import plotly.express as px
import locale

locale.setlocale(locale.LC_MONETARY, "pt_BR.UTF-8")

st.set_page_config(
    page_title="Comparação de compra de imóvel à vista vs financiado",
    page_icon="🏠",
    layout="wide",
)

st.title("Comparação de compra de imóvel à vista vs financiado")
st.markdown(
    """
Este aplicativo compara as implicações financeiras de comprar uma propriedade com pagamento à vista 
versus financiando-a. Insira seus parâmetros para ver a comparação. Estamos considerando que a propriedade
valoriza com o tempo e que a quantidade de dinheiro que você consegue guardar aumenta com a inflação, pois
teoricamente você recebe mais dinheiro, já que ele vale menos.
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
        value=2000,
        step=100,
    )

    monthly_inflation_rate = st.number_input(
        "Taxa de inflação mensal (%)", min_value=0.0, value=0.41, step=0.01
    )

    monthly_property_value_increase_when_bought = st.number_input(
        "Taxa de aumento do valor da propriedade depois de comprada por mês (%)",
        min_value=0.0,
        value=0.5,
        step=0.01,
    )


months_to_simulate = st.number_input(
    "Quantidade de meses a simular", min_value=1, value=120, step=1
)

monthly_savings = [float(initial_monthly_saving)]
months = [1]

for _ in range(months_to_simulate - 1):
    monthly_savings.append(monthly_savings[-1] * (1 + monthly_inflation_rate / 100))
    months.append(months[-1] + 1)

df = pd.DataFrame(
    {
        "mês": months,
        "economia mensal": monthly_savings,
    }
)

fig = px.line(
    df,
    x="mês",
    y="economia mensal",
    title="Quantidade de dinheiro que você deve guardar por mês",
)
st.plotly_chart(fig)


def simulate_property_purchase():
    st.markdown("## A vista")

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

    savings = [float(available_cash)]
    property_values = [float(property_value)]
    total_capital = [float(available_cash)]
    months_to_buy = None
    bought_property = False

    for i in range(months_to_simulate - 1):
        last_saving = savings[-1]
        new_saving = (
            last_saving * (1 + monthly_investment_return_rate / 100)
            + monthly_savings[i]
        )
        last_property_value = property_values[-1]
        if bought_property:
            new_property_value = last_property_value * (
                1 + monthly_property_value_increase_when_bought / 100
            )
        else:
            new_property_value = last_property_value * (
                1 + monthly_property_value_increase / 100
            )
        if new_saving > new_property_value and not bought_property:
            new_saving -= new_property_value
            bought_property = True
            months_to_buy = i
        savings.append(new_saving)
        property_values.append(new_property_value)
        total_capital.append(
            new_saving + (new_property_value if bought_property else 0)
        )
    df = pd.DataFrame(
        {
            "mês": months,
            "saldo": savings,
            "valor da propriedade": property_values,
            "capital total": total_capital,
        }
    )

    fig = px.line(
        df,
        x="mês",
        y=["saldo", "valor da propriedade", "capital total"],
        title="Saldo, valor da propriedade e capital total ao longo do tempo",
    )
    st.plotly_chart(fig)

    if months_to_buy is not None:
        st.success(
            f"Você terá dinheiro suficiente para comprar a propriedade à vista no mês {months_to_buy + 1} ({round((months_to_buy + 1) / 12, 2)} anos)."
        )
        st.write(
            f"Nesse momento, você terá {locale.currency(savings[months_to_buy], grouping=True)} e a propriedade valerá {locale.currency(property_values[months_to_buy], grouping=True)}.".replace(
                "R$", "R\\$"
            )
        )
        return months_to_buy + 1
    else:
        st.warning(
            "Dentro do período simulado, você não conseguirá juntar dinheiro suficiente para comprar a propriedade à vista."
        )
        return None


def simulate_property_purchase_financed():
    st.markdown("## Financiado")

    st.markdown(
        "Estamos levando em consideração que você vai pagar todo o valor que você consegue guardar "
        "mensalmente, abatendo parcelas futuras. Queremos saber quanto tempo vai demorar para você "
        "parar de pagar aluguel (se for o caso), para considerar que você vai ter mais dinheiro para "
        "economizar e pagar a dívida."
    )

    number_of_installments = st.number_input(
        "Quantidade de parcelas", min_value=1, value=270, step=1
    )

    tax = st.number_input(
        "Taxa de juros mensal (%)", min_value=0.0, value=0.91, step=0.01
    )

    current_rent = st.number_input(
        "Valor do aluguel atual ($)", min_value=0, value=1000, step=100
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

    st.write(
        f"Primeira parcela: {locale.currency(first_installment_value, grouping=True).replace('R$', 'R\\$')}"
    )

    if first_installment_value > monthly_savings[0]:
        st.warning(
            f"Você não tem dinheiro suficiente para pagar a primeira parcela. Tente aumentar a "
            "quantidade de parcelas ou a quantidade de dinheiro que você consegue guardar por mês."
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
        # Update future installment values
        for k in range(i, len(installment_values)):
            installment_values[k] *= 1 + tax / 100

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
            "mês": months[: len(need_to_pay)],
            "quantidade de dinheiro que vai faltar pagar": need_to_pay,
        }
    )

    fig = px.line(
        df,
        x="mês",
        y="quantidade de dinheiro que vai faltar pagar",
        title="Quantidade de dinheiro que vai faltar pagar por mês",
    )
    st.plotly_chart(fig)

    end_month = None

    for need_to_pay, month in zip(need_to_pay, months):
        if need_to_pay == 0:
            end_month = month
            break

    if end_month is not None:
        st.success(
            f"Você terminará de pagar a dívida no mês {end_month} ({round(end_month / 12, 2)} anos)."
        )
        return end_month
    else:
        st.warning(
            "Você não conseguirá terminar de pagar a dívida dentro do período simulado."
        )
        return None


end_month_to_buy_property_cash = simulate_property_purchase()
end_month_to_buy_property_financed = simulate_property_purchase_financed()

st.markdown("## Conclusão")

if (
    end_month_to_buy_property_cash is None
    and end_month_to_buy_property_financed is None
):
    st.warning("Você não conseguirá comprar a propriedade dentro do período simulado.")
elif end_month_to_buy_property_cash is None:
    st.success(
        f"Financiar é melhor que a vista. Se financiar, você terminará de pagar a dívida no mês "
        f"{end_month_to_buy_property_financed} ({round(end_month_to_buy_property_financed / 12, 2)} anos). "
        "Você não vai conseguir comprar a vista no período simulado."
    )
elif end_month_to_buy_property_financed is None:
    st.success(
        "Comprar à vista é melhor que financiar. Se comprar à vista, você terá dinheiro suficiente para "
        f"comprar a propriedade no mês {end_month_to_buy_property_cash} "
        f"({round(end_month_to_buy_property_cash / 12, 2)} anos). Você não vai conseguir comprar "
        "a vista no período simulado."
    )
else:
    if end_month_to_buy_property_cash < end_month_to_buy_property_financed:
        st.success(
            f"Comprar à vista é melhor que financiar. Se comprar à vista, você terminará de comprar a propriedade "
            f"no mês {end_month_to_buy_property_cash} ({round(end_month_to_buy_property_cash / 12, 2)} anos). "
            f"Já se financiar, você terminará de pagar a dívida no mês {end_month_to_buy_property_financed} "
            f"({round(end_month_to_buy_property_financed / 12, 2)} anos)."
        )
    else:
        st.success(
            f"Financiar é melhor que comprar à vista. Se financiar, você terminará de comprar a propriedade no mês "
            f"{end_month_to_buy_property_financed} ({round(end_month_to_buy_property_financed / 12, 2)} anos). "
            f"Já se comprar à vista, você conseguirá comprar a propriedade no mês "
            f"{end_month_to_buy_property_cash} ({round(end_month_to_buy_property_cash / 12, 2)} anos)."
        )
