
import math
import numpy as np


def _normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normal_pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def black_scholes(spot, strike, days, volatility, rate):
    """
    Return European call and put prices.
    Volatility and rate must be decimals.
    """

    spot = float(spot)
    strike = float(strike)
    days = float(days)
    volatility = float(volatility)
    rate = float(rate)

    if spot <= 0 or strike <= 0:
        raise ValueError("Spot and strike must be positive.")

    if days < 0:
        raise ValueError("Days cannot be negative.")

    if volatility <= 0:
        raise ValueError("Volatility must be positive.")

    if days == 0:
        return (
            max(spot - strike, 0.0),
            max(strike - spot, 0.0)
        )

    t = days / 365.0
    sqrt_t = math.sqrt(t)

    d1 = (
        math.log(spot / strike)
        + (rate + 0.5 * volatility**2) * t
    ) / (volatility * sqrt_t)

    d2 = d1 - volatility * sqrt_t

    call = (
        spot * _normal_cdf(d1)
        - strike * math.exp(-rate * t) * _normal_cdf(d2)
    )

    put = (
        strike * math.exp(-rate * t) * _normal_cdf(-d2)
        - spot * _normal_cdf(-d1)
    )

    return call, put


def calculate_payoff(
    strategy,
    prices,
    strike,
    premium,
    strike2=None,
    premium2=0.0
):
    """
    Calculate expiry profit/loss per underlying unit.
    """

    prices = np.asarray(prices, dtype=float)

    strike = float(strike)
    premium = float(premium)
    premium2 = float(premium2)

    if strike <= 0 or premium < 0 or premium2 < 0:
        raise ValueError("Invalid strike or premium.")

    if strategy == "Buy Call":
        return np.maximum(prices - strike, 0) - premium

    elif strategy == "Sell Call":
        return premium - np.maximum(prices - strike, 0)

    elif strategy == "Buy Put":
        return np.maximum(strike - prices, 0) - premium

    elif strategy == "Sell Put":
        return premium - np.maximum(strike - prices, 0)

    elif strategy == "Bull Call Spread":

        if strike2 is None or float(strike2) <= strike:
            raise ValueError("Upper strike must exceed lower strike.")

        strike2 = float(strike2)
        net_debit = premium - premium2

        return (
            np.maximum(prices - strike, 0)
            - np.maximum(prices - strike2, 0)
            - net_debit
        )

    else:
        raise ValueError(f"Unsupported strategy: {strategy}")


def strategy_metrics(
    strategy,
    strike,
    premium,
    lot_size,
    strike2=None,
    premium2=0.0
):
    """
    Calculate breakeven, maximum profit and maximum loss per lot.
    """

    strike = float(strike)
    premium = float(premium)
    lot_size = int(lot_size)
    premium2 = float(premium2)

    if strike <= 0 or premium < 0 or lot_size <= 0 or premium2 < 0:
        raise ValueError("Invalid financial inputs.")

    if strategy == "Buy Call":

        return {
            "breakeven": strike + premium,
            "max_profit": math.inf,
            "max_loss": premium * lot_size,
            "net_debit": premium
        }

    elif strategy == "Sell Call":

        return {
            "breakeven": strike + premium,
            "max_profit": premium * lot_size,
            "max_loss": math.inf,
            "net_debit": -premium
        }

    elif strategy == "Buy Put":

        be = strike - premium

        return {
            "breakeven": be if be > 0 else None,
            "max_profit": max(strike - premium, 0) * lot_size,
            "max_loss": premium * lot_size,
            "net_debit": premium
        }

    elif strategy == "Sell Put":

        be = strike - premium

        return {
            "breakeven": be if be > 0 else None,
            "max_profit": premium * lot_size,
            "max_loss": max(strike - premium, 0) * lot_size,
            "net_debit": -premium
        }

    elif strategy == "Bull Call Spread":

        if strike2 is None or float(strike2) <= strike:
            raise ValueError("Upper strike must exceed lower strike.")

        strike2 = float(strike2)

        net_debit = premium - premium2
        width = strike2 - strike

        be = (
            strike + net_debit
            if 0 <= net_debit <= width
            else None
        )

        return {
    "breakeven": be,
    "max_profit": (width - net_debit) * lot_size,
    "max_loss": max(net_debit, 0) * lot_size,
    "minimum_profit": max(-net_debit, 0) * lot_size,
    "net_debit": net_debit
}

    else:
        raise ValueError(f"Unsupported strategy: {strategy}")


def calculate_greeks(
    spot,
    strike,
    days,
    volatility,
    rate,
    option_type="call"
):
    """
    European Black-Scholes Greeks.

    Theta: per calendar day.
    Vega: per 1 percentage-point volatility change.
    Rho: per 1 percentage-point interest rate change.
    """

    spot = float(spot)
    strike = float(strike)
    days = float(days)
    volatility = float(volatility)
    rate = float(rate)

    if spot <= 0 or strike <= 0:
        raise ValueError("Spot and strike must be positive.")

    if days <= 0:
        return {
            "delta": None,
            "gamma": None,
            "theta": None,
            "vega": None,
            "rho": None
        }

    if volatility <= 0:
        raise ValueError("Volatility must be positive.")

    t = days / 365.0
    sqrt_t = math.sqrt(t)

    d1 = (
        math.log(spot / strike)
        + (rate + 0.5 * volatility**2) * t
    ) / (volatility * sqrt_t)

    d2 = d1 - volatility * sqrt_t

    pdf = _normal_pdf(d1)

    discounted_strike = strike * math.exp(-rate * t)

    gamma = pdf / (spot * volatility * sqrt_t)

    vega = spot * pdf * sqrt_t / 100.0

    if option_type.lower() == "call":

        delta = _normal_cdf(d1)

        theta_annual = (
            -(spot * pdf * volatility) / (2 * sqrt_t)
            - rate * discounted_strike * _normal_cdf(d2)
        )

        rho = (
            discounted_strike * t * _normal_cdf(d2) / 100.0
        )

    elif option_type.lower() == "put":

        delta = _normal_cdf(d1) - 1.0

        theta_annual = (
            -(spot * pdf * volatility) / (2 * sqrt_t)
            + rate * discounted_strike * _normal_cdf(-d2)
        )

        rho = (
            -discounted_strike * t * _normal_cdf(-d2) / 100.0
        )

    else:
        raise ValueError("Option type must be call or put.")

    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta_annual / 365.0,
        "vega": vega,
        "rho": rho
    }
