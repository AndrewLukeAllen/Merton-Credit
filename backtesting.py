import pandas as pd
import numpy as np

from merton_model import MertonModel

class MertonBacktester:

    def __init__(self,company_id,market_data, financials, volatility_window=252,
        maturity=1, risk_free_rate=0.00):

        self.company_id = company_id
        self.market_data = market_data.copy()
        self.financials = financials.copy()

        self.volatility_window = volatility_window
        self.maturity = maturity
        self.risk_free_rate = risk_free_rate

        self.results = None

    def run(self):

        market_data = self.market_data.sort_values("date").copy()
        financials = self.financials.sort_values(["filing_date", "period_end"]).copy()

        results = []

        for _, row in market_data.iterrows():

            current_date = row["date"]

            # Get finnanical data available at time

            available_financials = financials[financials["filing_date"] <= current_date]

            if available_financials.empty:
                continue

            latest_filing_date = available_financials["filing_date"].max()
            latest_filing = available_financials[available_financials["filing_date"] == latest_filing_date]
            latest_financials = latest_filing.loc[latest_filing["period_end"].idxmax()]

            shares = latest_financials["ordinary_shares"]
            debt = latest_financials["total_debt"]

            financial_filing_date = latest_financials["filing_date"]
            financial_period_end = latest_financials["period_end"]

            # Get prices upto current_datae

            historical_prices = market_data[market_data["date"] <= current_date].tail(self.volatility_window + 1)

            if len(historical_prices) < self.volatility_window:
                continue

            # Calc equity

            stock_price = row["close"]

            # Some div by 0 are sneaking in and we need to know where

            if pd.isna(shares) or shares <= 0:
                continue

            if pd.isna(debt) or debt <= 0:
                continue

            if pd.isna(stock_price) or stock_price <= 0:
                continue

            equity_value = shares * stock_price

            # run Merton

            try:

                model = MertonModel(equity_value=equity_value, prices=historical_prices,
                    debt=debt, maturity=self.maturity, risk_free_rate=self.risk_free_rate)

                result = model.run()

            except (ValueError, RuntimeError, FloatingPointError):
                continue

            # Store the result

            result["company_id"] = self.company_id
            result["date"] = current_date

            result["financial_filing_date"] = financial_filing_date
            result["financial_period_end"] = financial_period_end

            results.append(result)

        self.results = pd.DataFrame(results)

        return self.results