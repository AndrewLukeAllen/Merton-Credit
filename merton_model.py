import numpy as np


from scipy.optimize import root
from scipy.stats import norm

def calc_equity_vol(prices):

    # May change toi GARCH in the future

    prices = prices.sort_values("date")

    returns = np.log(prices["close"] / prices["close"].shift(1))
    volatility = returns.std() * np.sqrt(252)

    return volatility


# Implemented Merton model based off  https://www.investopedia.com/terms/m/mertonmodel.asp and
# https://www.sciencedirect.com/topics/social-sciences/distance-to-default . Includes summary/ explanation of the formulas
class MertonModel:

    def __init__(self, equity_value, prices, debt, maturity, risk_free_rate = 0.00):

        # we commited some oopsies inspricing this
        if equity_value <= 0:
            raise ValueError("Equity value must be positive")

        if debt <= 0:
            raise ValueError("Debt must be positive")

        if maturity <= 0:
            raise ValueError("Maturity must be positive")

        if prices.empty:
            raise ValueError("Price data is empty")

        self.equity_value = equity_value
        self.equity_volatility = calc_equity_vol(prices)
        self.debt = debt
        self.risk_free_rate = risk_free_rate
        self.maturity = maturity

        self.asset_value = None
        self.asset_volatility = None
        self.distance_to_default = None
        self.probability_of_default = None

    def solve_asset_values(self):

        def equations(x):
            # see https://www.investopedia.com/terms/m/mertonmodel.asp for a summary/ explanation
            # of the formulas

            asset_value, asset_volatility = x

            d1 = (np.log(asset_value / self.debt)
                + (self.risk_free_rate + 0.5 * asset_volatility**2
                ) * self.maturity
            ) / (asset_volatility * np.sqrt(self.maturity))

            d2 = d1 - (asset_volatility * np.sqrt(self.maturity))

            calculated_equity = (
                asset_value * norm.cdf(d1)
                - self.debt
                * np.exp(
                    -self.risk_free_rate
                    * self.maturity
                )
                * norm.cdf(d2)
            )

            calculated_equity_volatility = (
                asset_value / self.equity_value * norm.cdf(d1)* asset_volatility)

            return [
                calculated_equity - self.equity_value,
                calculated_equity_volatility - self.equity_volatility
            ]

        initial_guess = [
            self.equity_value + self.debt,
            self.equity_volatility
        ]

        result = root(equations, initial_guess)

        if not result.success:
            raise ValueError(
                "Merton model failed to converge"
            )

        self.asset_value = result.x[0]
        self.asset_volatility = result.x[1]

        return self.asset_value, self.asset_volatility

    def calculate_distance_to_default(self):

        if self.asset_value is None:
            self.solve_asset_values()

        self.distance_to_default = (
            np.log(self.asset_value / self.debt)
            + (
                self.risk_free_rate
                - 0.5 * self.asset_volatility**2
            ) * self.maturity
        ) / (
            self.asset_volatility
            * np.sqrt(self.maturity)
        )

        return self.distance_to_default

    def calculate_probability_of_default(self):

        if self.distance_to_default is None:
            self.calculate_distance_to_default()

        self.probability_of_default = norm.cdf(
            -self.distance_to_default
        )

        return self.probability_of_default

    def run(self):

        self.solve_asset_values()
        self.calculate_distance_to_default()
        self.calculate_probability_of_default()

        # i got tired of writing float() and used chatgpt to do it for me
        # is this more typing than doing it myself, yes, oh well.
        return {
            "equity_value": float(self.equity_value),
            "equity_volatility": float(self.equity_volatility),
            "default_barrier": float(self.debt),
            "asset_value": float(self.asset_value),
            "asset_volatility": float(self.asset_volatility),
            "distance_to_default": float(self.distance_to_default),
            "probability_of_default": float(
                self.probability_of_default
            )
        }
               