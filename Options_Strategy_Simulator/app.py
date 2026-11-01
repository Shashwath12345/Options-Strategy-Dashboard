
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from finance_functions import (
    black_scholes,
    calculate_greeks,
    calculate_payoff,
    strategy_metrics,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Options Strategy Simulator",
    page_icon="📈",
    layout="wide",
)


# ==================================================
# CUSTOM DESIGN
# ==================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b1220;
        color: #e8eef7;
    }

    [data-testid="stSidebar"] {
        background-color: #121d2e;
    }

    [data-testid="stMetric"] {
        background-color: #121d2e;
        border: 1px solid #2a3a50;
        padding: 16px;
        border-radius: 10px;
    }

    h1, h2, h3 {
        color: #e8eef7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# HEADER
# ==================================================

st.markdown(
    "<h4 style='color:#20c997;'>FINANCE LAB</h4>",
    unsafe_allow_html=True,
)

st.title("Options Strategy Simulator")

st.caption(
    "Analyse, simulate and compare options trading strategies."
)



# ==================================================
# SIDEBAR INPUTS AND INTERACTIVE BUTTONS
# ==================================================

# Default values

DEFAULTS = {
    "strategy": "Buy Call",
    "spot": 2500,
    "strike": 2500.0,
    "premium": 85.0,
    "days": 30,
    "volatility": 25.0,
    "rate": 6.5,
    "lot_size": 25,
    "strike2": 2700.0,
    "premium2": 30.0,
}


# Initialize session state

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# Reset callback

def reset_inputs():

    for key, value in DEFAULTS.items():
        st.session_state[key] = value


# Black-Scholes premium callback

def use_bs_premium():

    s = float(st.session_state.spot)
    k = float(st.session_state.strike)
    d = int(st.session_state.days)
    v = float(st.session_state.volatility) / 100
    r = float(st.session_state.rate) / 100

    call, put = black_scholes(s, k, d, v, r)

    selected_strategy = st.session_state.strategy

    if selected_strategy in ["Buy Put", "Sell Put"]:
        st.session_state.premium = round(put, 2)

    else:
        st.session_state.premium = round(call, 2)


# Sidebar

with st.sidebar:

    st.header("Trade Configuration")

    strategy = st.selectbox(
        "Select Strategy",
        [
            "Buy Call",
            "Sell Call",
            "Buy Put",
            "Sell Put",
            "Bull Call Spread",
        ],
        key="strategy",
    )

    st.subheader("Underlying Information")

    spot = st.slider(
        "Underlying Price (₹)",
        100,
        10000,
        key="spot",
    )

    strike = st.number_input(
        "Strike Price (₹)",
        min_value=1.0,
        step=25.0,
        key="strike",
    )

    premium = st.number_input(
        "Option Premium (₹)",
        min_value=0.0,
        step=1.0,
        key="premium",
    )

    days = st.slider(
        "Days to Expiry",
        0,
        730,
        key="days",
    )

    volatility = st.slider(
        "Volatility (%)",
        1.0,
        150.0,
        step=0.5,
        key="volatility",
    )

    rate = st.number_input(
        "Risk-free Rate (%)",
        step=0.25,
        key="rate",
    )

    lot_size = st.number_input(
        "Lot Size",
        min_value=1,
        step=1,
        key="lot_size",
    )

    # Bull Call Spread inputs

    strike2 = float(strike) + 200.0
    premium2 = 30.0

    if strategy == "Bull Call Spread":

        st.subheader("Spread Configuration")

        # Keep upper strike above lower strike
        if st.session_state.strike2 <= strike:
            st.session_state.strike2 = float(strike) + 200.0

        strike2 = st.number_input(
            "Upper Strike (₹)",
            min_value=float(strike) + 1.0,
            step=25.0,
            key="strike2",
        )

        premium2 = st.number_input(
            "Short Call Premium (₹)",
            min_value=0.0,
            step=1.0,
            key="premium2",
        )

    st.divider()

    # Black-Scholes button

    st.button(
        "Use Black–Scholes Price as Premium",
        on_click=use_bs_premium,
        use_container_width=True,
    )

    if strategy == "Bull Call Spread":
        st.caption(
            "This fills the theoretical premium of the long call. "
            "Enter the short call premium separately."
        )

    # Reset button

    st.button(
        "Reset to Defaults",
        on_click=reset_inputs,
        use_container_width=True,
    )

    st.caption(
        "Educational model | European options"
    )


# ==================================================
# FINANCIAL CALCULATIONS
# ==================================================

vol = volatility / 100.0
risk_rate = rate / 100.0


try:

    call_price, put_price = black_scholes(
        float(spot),
        float(strike),
        int(days),
        vol,
        risk_rate,
    )

    metrics = strategy_metrics(
        strategy,
        float(strike),
        float(premium),
        int(lot_size),
        strike2=float(strike2),
        premium2=float(premium2),
    )

    breakeven = metrics["breakeven"]

    selected_bs_price = (
        put_price
        if strategy in ("Buy Put", "Sell Put")
        else call_price
    )

    # ==================================================
    # CHART RANGE AND PAYOFF
    # ==================================================

    x_min = max(
        0.0,
        min(float(spot) * 0.45, float(strike) * 0.45),
    )

    x_max = max(
        float(spot) * 1.65,
        float(strike) * 1.60,
        float(strike2) * 1.15,
    )

    if breakeven is not None:

        x_min = min(
            x_min,
            max(0.0, breakeven * 0.85),
        )

        x_max = max(
            x_max,
            breakeven * 1.15,
        )

    prices = np.linspace(x_min, x_max, 450)

    pnl = calculate_payoff(
        strategy,
        prices,
        float(strike),
        float(premium),
        float(strike2),
        float(premium2),
    ) * int(lot_size)

    def format_money(value):

        if value is None:
            return "N/A"

        if math.isinf(value):
            return "Unlimited"

        return f"₹{value:,.2f}"

    # ==================================================
    # STRATEGY OVERVIEW
    # ==================================================

    st.subheader("Strategy Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Breakeven",
        format_money(breakeven),
    )

    col2.metric(
        "Maximum Profit",
        format_money(metrics["max_profit"]),
    )

    col3.metric(
        "Maximum Loss",
        format_money(metrics["max_loss"]),
    )

    selected_bs_label = (
        "Black–Scholes Put"
        if strategy in ("Buy Put", "Sell Put")
        else "Black–Scholes Call"
    )

    col4.metric(
        selected_bs_label,
        f"₹{selected_bs_price:,.2f}",
    )

    # ==================================================
    # PAYOFF CHART
    # ==================================================

    st.divider()

    st.subheader("Profit / Loss at Expiry")

    fig = go.Figure()

    # Profit zone

    fig.add_trace(
        go.Scatter(
            x=prices,
            y=np.where(pnl >= 0, pnl, 0),
            fill="tozeroy",
            mode="none",
            fillcolor="rgba(32,201,151,0.22)",
            name="Profit Zone",
            hoverinfo="skip",
        )
    )

    # Loss zone

    fig.add_trace(
        go.Scatter(
            x=prices,
            y=np.where(pnl < 0, pnl, 0),
            fill="tozeroy",
            mode="none",
            fillcolor="rgba(255,107,107,0.25)",
            name="Loss Zone",
            hoverinfo="skip",
        )
    )

    # Payoff curve

    fig.add_trace(
        go.Scatter(
            x=prices,
            y=pnl,
            mode="lines",
            name="Profit / Loss",
            line=dict(
                color="#20c997",
                width=3.5,
            ),
            hovertemplate=(
                "Underlying: ₹%{x:,.2f}<br>"
                "Profit / Loss per lot: ₹%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    # Zero profit line

    fig.add_hline(
        y=0,
        line_color="#d1d5db",
        line_width=1.2,
    )

    # Spot price

    fig.add_vline(
        x=spot,
        line_dash="dot",
        line_color="#f6c85f",
        line_width=2,
    )

    fig.add_annotation(
        x=spot,
        y=1.13,
        xref="x",
        yref="paper",
        text=f"SPOT: ₹{spot:,.0f}",
        showarrow=False,
        xanchor="right",
        font=dict(
            color="#f6c85f",
            size=11,
        ),
        bgcolor="rgba(20,30,45,0.9)",
    )

    # Breakeven

    if breakeven is not None:

        fig.add_vline(
            x=breakeven,
            line_dash="dash",
            line_color="#65a8ff",
            line_width=2,
        )

        fig.add_annotation(
            x=breakeven,
            y=1.06,
            xref="x",
            yref="paper",
            text=f"BREAKEVEN: ₹{breakeven:,.2f}",
            showarrow=False,
            xanchor="left",
            font=dict(
                color="#65a8ff",
                size=11,
            ),
            bgcolor="rgba(20,30,45,0.9)",
        )

    # Maximum profit

    if math.isinf(metrics["max_profit"]):

        fig.add_annotation(
            x=0.98,
            y=0.94,
            xref="paper",
            yref="paper",
            text="MAX PROFIT: UNLIMITED",
            showarrow=False,
            xanchor="right",
            font=dict(
                color="#20c997",
                size=11,
            ),
        )

    else:

        fig.add_hline(
            y=metrics["max_profit"],
            line_dash="dash",
            line_color="#20c997",
            line_width=1.8,
            annotation_text=(
                f"MAX PROFIT: ₹{metrics['max_profit']:,.2f}"
            ),
            annotation_position="top right",
            annotation_font_color="#20c997",
        )

    # Maximum loss

    if math.isinf(metrics["max_loss"]):

        fig.add_annotation(
            x=0.98,
            y=0.06,
            xref="paper",
            yref="paper",
            text="MAX LOSS: UNLIMITED",
            showarrow=False,
            xanchor="right",
            font=dict(
                color="#ff6b6b",
                size=11,
            ),
        )

    elif metrics["max_loss"] > 0:

        fig.add_hline(
            y=-metrics["max_loss"],
            line_dash="dash",
            line_color="#ff6b6b",
            line_width=1.8,
            annotation_text=(
                f"MAX LOSS: ₹{metrics['max_loss']:,.2f}"
            ),
            annotation_position="bottom right",
            annotation_font_color="#ff6b6b",
        )

    # Chart layout

    fig.update_layout(
        template="plotly_dark",
        height=600,
        paper_bgcolor="#121d2e",
        plot_bgcolor="#121d2e",
        title=dict(
            text=f"{strategy} | Expiry Payoff",
            font=dict(
                size=19,
                color="#e8eef7",
            ),
        ),
        xaxis_title="Underlying Price at Expiry (₹)",
        yaxis_title="Profit / Loss per Lot (₹)",
        hovermode="x unified",
        margin=dict(
            l=25,
            r=35,
            t=110,
            b=70,
        ),
        legend=dict(
            orientation="h",
            y=-0.18,
            x=0,
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#2a3a50",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#2a3a50",
            zeroline=True,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "displaylogo": False,
        },
    )

    # ==================================================
    # BLACK-SCHOLES PRICING
    # ==================================================

    st.divider()

    st.subheader("Black–Scholes Pricing")

    bs1, bs2, bs3 = st.columns(3)

    bs1.metric(
        "Theoretical Call Price",
        f"₹{call_price:,.2f}",
    )

    bs2.metric(
        "Theoretical Put Price",
        f"₹{put_price:,.2f}",
    )

    bs3.metric(
        "Selected Option Theoretical Price",
        f"₹{selected_bs_price:,.2f}",
    )

    # ==================================================
    # OPTION GREEKS AND MONEYNESS
    # ==================================================

    st.divider()

    st.subheader("Option Greeks & Moneyness")

    option_type = (
        "put"
        if strategy in ("Buy Put", "Sell Put")
        else "call"
    )

    greeks = calculate_greeks(
        float(spot),
        float(strike),
        int(days),
        vol,
        risk_rate,
        option_type,
    )

    # Reverse Greeks for short options

    if strategy in ("Sell Call", "Sell Put"):

        greeks = {
            key: (
                -value
                if value is not None
                else None
            )
            for key, value in greeks.items()
        }

    # Net Greeks for Bull Call Spread

    if strategy == "Bull Call Spread":

        short_greeks = calculate_greeks(
            float(spot),
            float(strike2),
            int(days),
            vol,
            risk_rate,
            "call",
        )

        if greeks["delta"] is not None:

            greeks = {
                key: greeks[key] - short_greeks[key]
                for key in greeks
            }

    # Moneyness

    if abs(float(spot) - float(strike)) / float(strike) <= 0.01:

        moneyness = "ATM"

    elif option_type == "call":

        moneyness = (
            "ITM" if spot > strike else "OTM"
        )

    else:

        moneyness = (
            "ITM" if spot < strike else "OTM"
        )

    st.markdown(
        f"**Selected option moneyness: {moneyness}**"
    )

    if strategy == "Bull Call Spread":

        st.caption(
            "Greeks shown are net position Greeks: "
            "long lower-strike call minus short upper-strike call."
        )

    def greek_display(value):

        return (
            "N/A"
            if value is None
            else f"{value:.5f}"
        )

    greek_columns = st.columns(5)

    greek_items = [
        ("Delta", "delta"),
        ("Gamma", "gamma"),
        ("Theta / day", "theta"),
        ("Vega / 1% vol", "vega"),
        ("Rho / 1% rate", "rho"),
    ]

    for column, (label, key) in zip(
        greek_columns,
        greek_items,
    ):

        column.metric(
            label,
            greek_display(greeks[key]),
        )

    st.caption(
        "Theta is per calendar day. Vega and Rho are per "
        "one percentage-point change. At expiry, Greeks "
        "are shown as N/A."
    )

    # ==================================================
    # PREMIUM VALUATION
    # ==================================================

    st.subheader("Premium Valuation")

    premium_difference = (
        float(premium) - selected_bs_price
    )

    val1, val2, val3 = st.columns(3)

    val1.metric(
        "Entered Premium",
        f"₹{premium:,.2f}",
    )

    val2.metric(
        "Theoretical Premium",
        f"₹{selected_bs_price:,.2f}",
    )

    val3.metric(
        "Premium Difference",
        f"₹{premium_difference:+,.2f}",
    )

    if premium_difference > 0.01:

        st.warning(
            "Entered premium is above the theoretical "
            "Black–Scholes price. This is a model comparison, "
            "not proof of market mispricing."
        )

    elif premium_difference < -0.01:

        st.success(
            "Entered premium is below the theoretical "
            "Black–Scholes price. This is a model comparison, "
            "not proof of market mispricing."
        )

    else:

        st.info(
            "Entered premium approximately matches "
            "the theoretical Black–Scholes price."
        )

    # ==================================================
    # SCENARIO ANALYSIS
    # ==================================================

    st.divider()

    st.subheader("Scenario Analysis")

    scenario_changes = [-10, -5, 0, 5, 10]

    scenario_data = []

    for change in scenario_changes:

        future_price = float(spot) * (
            1.0 + change / 100.0
        )

        scenario_pnl = calculate_payoff(
            strategy,
            np.array([future_price]),
            float(strike),
            float(premium),
            float(strike2),
            float(premium2),
        )[0] * int(lot_size)

        scenario_data.append(
            {
                "Underlying Change": f"{change:+}%",
                "Future Price": f"₹{future_price:,.2f}",
                "Profit / Loss per Lot": f"₹{scenario_pnl:,.2f}",
            }
        )

    st.dataframe(
        pd.DataFrame(scenario_data),
        use_container_width=True,
        hide_index=True,
    )

    # ==================================================
    # BUSINESS INSIGHTS
    # ==================================================

    st.divider()

    st.subheader("Strategy Interpretation")

    be_text = format_money(breakeven)

    if strategy == "Buy Call":

        insight = (
            f"A Buy Call is suited to a bullish outlook. "
            f"The breakeven at expiry is {be_text}. "
            f"Maximum loss is {format_money(metrics['max_loss'])} "
            f"per lot, while profit potential is unlimited. "
            "Time decay generally hurts long options; "
            "higher volatility generally increases option value."
        )

    elif strategy == "Sell Call":

        insight = (
            f"A Sell Call receives a premium of ₹{premium:,.2f} "
            f"per share. Maximum profit is "
            f"{format_money(metrics['max_profit'])} per lot, "
            f"while maximum loss is unlimited. Breakeven is "
            f"{be_text}. It is generally used with a bearish-to-neutral "
            "outlook. Time decay generally benefits the short option, "
            "while rising volatility generally hurts it."
        )

    elif strategy == "Buy Put":

        insight = (
            f"A Buy Put is suited to a bearish outlook or downside "
            f"protection. Breakeven is {be_text}. Maximum profit is "
            f"{format_money(metrics['max_profit'])} per lot and "
            f"maximum loss is {format_money(metrics['max_loss'])} "
            f"per lot. Time decay generally hurts long options; "
            "higher volatility generally helps."
        )

    elif strategy == "Sell Put":

        insight = (
            f"A Sell Put receives a premium of ₹{premium:,.2f} "
            f"per share. Maximum profit is "
            f"{format_money(metrics['max_profit'])} per lot and "
            f"maximum loss is {format_money(metrics['max_loss'])} "
            f"per lot. Breakeven is {be_text}. It is generally used "
            "with a bullish-to-neutral outlook. Time decay generally "
            "benefits the short option, while rising volatility "
            "generally hurts it."
        )

    else:

        net_debit = metrics["net_debit"]

        debit_or_credit = (
            "net debit"
            if net_debit >= 0
            else "net credit"
        )

        insight = (
            f"A Bull Call Spread is suited to a moderately bullish "
            f"outlook. The position has a {debit_or_credit} of "
            f"₹{abs(net_debit):,.2f} per share. Maximum profit is "
            f"{format_money(metrics['max_profit'])} per lot and "
            f"maximum loss is {format_money(metrics['max_loss'])} "
            f"per lot. Breakeven is {be_text}. The short call offsets "
            "some time decay and volatility exposure compared "
            "with a long call."
        )

    st.info(insight)

    # ============================================================
    # RISK, REWARD & CAPITAL EFFICIENCY
    # ============================================================

    st.markdown("---")
    st.subheader("Risk, Reward & Capital Efficiency")

    col1, col2, col3 = st.columns(3)

    max_profit = metrics.get("max_profit", 0)
    max_loss = metrics.get("max_loss", 0)

    with col1:
        if np.isinf(max_profit):
            st.metric("Maximum Profit", "Unlimited")
        else:
            st.metric("Maximum Profit", f"₹{max_profit:,.2f}")

    with col2:
        if np.isinf(max_loss):
            st.metric("Maximum Loss", "Unlimited")
        else:
            st.metric("Maximum Loss", f"₹{abs(max_loss):,.2f}")

    with col3:
        if np.isinf(max_profit) and np.isfinite(max_loss):
            st.metric("Reward-to-Risk", "Unlimited")
        elif np.isinf(max_loss):
            st.metric("Reward-to-Risk", "Unfavourable")
        elif max_loss == 0:
            st.metric("Reward-to-Risk", "N/A")
        else:
            ratio = max_profit / abs(max_loss)
            st.metric("Reward-to-Risk", f"{ratio:.2f}:1")

    # Return on initial premium or debit
    st.markdown("#### Maximum Return on Initial Investment")

    if strategy == "Buy Call":
        st.info("Theoretical upside is unlimited. Maximum return cannot be expressed as a fixed percentage.")
    elif strategy == "Buy Put":
        if premium > 0:
            return_pct = (max_profit / premium) * 100
            st.metric("Maximum Return on Premium Paid", f"{return_pct:.2f}%")
        else:
            st.write("Maximum return cannot be calculated because the premium is zero.")
    elif strategy in ["Sell Call", "Sell Put"]:
        st.metric("Maximum Return on Premium Received", "100%")
        st.caption("This is based on premium received, not the margin or capital required to maintain the position.")
    elif strategy == "Bull Call Spread":
        if premium > 0:
            return_pct = (max_profit / premium) * 100
            st.metric("Maximum Return on Net Debit", f"{return_pct:.2f}%")
        else:
            st.write("Maximum return on net debit is not applicable.")

    st.caption(
        "These are theoretical expiry-based payoff figures. "
        "They exclude brokerage, taxes, slippage and margin requirements."
    )

    # ============================================================
    # BUSINESS INSIGHT
    # ============================================================

    st.markdown("---")
    st.subheader("Business Insight")

    business_insights = {
        "Buy Call": (
            "This strategy is suitable when an investor expects a significant rise "
            "in the underlying asset. The maximum loss is limited to the premium paid, "
            "while the potential profit is unlimited. Time decay works against the buyer."
        ),
        "Sell Call": (
            "This strategy is suitable when an investor expects the underlying asset "
            "to remain below the strike price. The maximum gain is limited to the "
            "premium received, while potential losses are unlimited. Rising volatility "
            "and upward price movements increase risk."
        ),
        "Buy Put": (
            "This strategy is suitable when an investor expects the underlying asset "
            "to decline. It can also provide downside protection for an existing "
            "portfolio. The maximum loss is limited to the premium paid."
        ),
        "Sell Put": (
            "This strategy is suitable when an investor expects the underlying asset "
            "to remain stable or rise. The maximum gain is limited to the premium "
            "received, while substantial losses can occur if the asset price falls."
        ),
        "Bull Call Spread": (
            "This strategy is suitable when an investor expects a moderate increase "
            "in the underlying asset. It reduces the initial cost compared with buying "
            "a call outright, but also caps the maximum potential profit."
        )
    }

    st.info(business_insights.get(strategy, "No business insight available."))

    # ==================================================
    # MODEL ASSUMPTIONS AND LIMITATIONS
    # ==================================================

    with st.expander(
        "Model Assumptions and Limitations"
    ):

        st.write(
            """
            - European options are assumed for Black–Scholes pricing.
            - Black–Scholes assumes constant volatility and a constant risk-free rate.
            - No dividends are included.
            - Brokerage, taxes, slippage and liquidity costs are excluded.
            - Payoff charts show expiry profit/loss, not changing market value before expiry.
            - Short-call losses are theoretically unlimited.
            - Short-put losses are substantial but bounded by the underlying price reaching zero.
            - This is an educational simulator, not investment advice.
            """
        )


except (ValueError, TypeError, ZeroDivisionError) as error:

    st.error(f"Input or calculation error: {error}")


except Exception as error:

    st.error(f"Unexpected application error: {error}")
