import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt 

from Data.Database import (
    session,
    create_tables,
    Company,
    MarketData,
    Financials
)

from Data.Importing import (
    download_share_data,
    store_share_data,
    store_fin_data,
    import_fin_data,
    store_fin_data,
    download_share_data_sec
)

from merton_model import MertonModel
from backtesting import MertonBacktester, WasMertonRight

from sqlalchemy import select
from test import import_total_debt_SEC

# Constants
TICKER = "GOOG"
START_DATE = "2020-01-01"
END_DATE = "2025-12-31"


# create_tables()

# google = Company(
#     ticker="GOOG",
#     sector="Technology",
#     company_name="Alphabet Inc."
# )

# session.add(google)
# session.commit()

company = (
    session.query(Company)
    .filter_by(ticker=TICKER)
    .first()
)

if company is None:
    raise ValueError(f"{TICKER} does not exist in the database.")

company_id = company.company_id

print(f"{TICKER} company_id = {company_id}")

# Download Share data
prices = download_share_data(TICKER,START_DATE,END_DATE)
store_share_data(prices,session)

# Download Finnancial Data
fin_data = import_fin_data(TICKER,2020,2025)
store_fin_data(fin_data,TICKER,session)

# Test if this all plays nice with the Merton Model

stmt = select(Financials.ordinary_shares).where(Financials.company_id == company_id)
shares = session.scalars(stmt).all()

stmt = select(MarketData.close, MarketData.date).where(MarketData.company_id == company_id)
price = pd.read_sql(stmt,session.bind,columns=["close", "date"])

stmt = select(Financials.total_debt).where(Financials.company_id == company_id)
debt = session.scalars(stmt).all()

equity_val = shares[-1] * price["close"].iloc[-1]
m = MertonModel(equity_val,price,debt[-1],1)
results = m.run()

print(results)

# We now test the backtester ha

stmt = select(MarketData.close,MarketData.date).where(MarketData.company_id == company_id).order_by(MarketData.date)
price = pd.read_sql(stmt, session.bind)

stmt = (
    select(
        Financials.filing_date,
        Financials.period_end,
        Financials.total_debt,
        Financials.ordinary_shares,
        Financials.fiscal_period,
        Financials.fiscal_year
    )
    .where(Financials.company_id == 1)
    .order_by(Financials.filing_date)
)

financials = pd.read_sql(stmt, session.bind)

print(
    financials[
        [
            "filing_date",
            "period_end",
            "total_debt",
            "ordinary_shares",
            "fiscal_period",
            "fiscal_year",
        ]
    ].tail(10)
)

backtester = MertonBacktester(
    company_id=1,
    market_data=price,
    financials=financials,
    volatility_window=252,
    maturity=1,
    risk_free_rate=0.00
)

results = backtester.run()

print(results)

plt.figure(figsize=(12, 6))

plt.plot(
    results["date"],
    results["distance_to_default"],
    linewidth=2,
    color="steelblue"
)

plt.xlabel("Date")
plt.ylabel("Distance to Default")
plt.title(f"Distance to Default — Company {results['company_id'].iloc[0]}")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
plt.close()


##### LEt's see if our model can actually do something

# Constants
TICKER = "F"
START_DATE = "2007-01-01"
END_DATE = "2008-12-31"

# ford = Company(
#     ticker="F",
#     sector="Cars",
#     company_name="Ford"
# )

# session.add(ford)
# session.commit()

company = (
    session.query(Company)
    .filter_by(ticker=TICKER)
    .first()
)

if company is None:
    raise ValueError(f"{TICKER} does not exist in the database.")

company_id = company.company_id

print(f"{TICKER} company_id = {company_id}")

# Download Share data
prices = download_share_data(TICKER,START_DATE,END_DATE)
store_share_data(prices,session)

# Download Finnancial Data

pls_work = import_total_debt_SEC("0000037996",2007,2008)

print(pls_work.to_string(index=False))



# Test if this all plays nice with the Merton Model

stmt = select(MarketData.close, MarketData.date).where(MarketData.company_id == company_id)
price = pd.read_sql(stmt,session.bind,columns=["close", "date"])

equity_val = pls_work["ordinary_shares"].iloc[0] * price["close"].iloc[-1]
m = MertonModel(equity_val,price,pls_work["total_debt"].iloc[0],1)
results = m.run()

print(results)

print(f"Simple debt / equity is = {pls_work["total_debt"].iloc[0] / equity_val}")
# IT is doing terribly and will crash, almost 5x what it is now days

# Test backtest 
stmt = select(MarketData.close,MarketData.date).where(MarketData.company_id == company_id).order_by(MarketData.date)
price = pd.read_sql(stmt, session.bind)

backtester = MertonBacktester(
    company_id=2,
    market_data=price,
    financials=pls_work,
    volatility_window=252,
    maturity=1,
    risk_free_rate=0.00
)

results = backtester.run()

print(results)

results["date"] = pd.to_datetime(results["date"])
results = results.sort_values("date")

plt.figure(figsize=(12, 6))

plt.plot(
    results["date"],
    results["distance_to_default"],
    linewidth=2,
    color="steelblue"
)

plt.xlabel("Date")
plt.ylabel("Distance to Default")
plt.title(f"Distance to Default — Company {results['company_id'].iloc[0]}")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
plt.close()



# We are going to say the distress event was at the end of 2008
# in actuality it happened ~march of 2009, but to keep the in progress 
# testing of the testing we will say it happened on 12-31-2008
# which is close enough in some limited sense as this is when
# tehy based their restructuing around.

distress_events = pd.DataFrame({
    "company_id": [2, 2],
    "event_date": pd.to_datetime([
        "2008-09-15",
        "2008-11-01",
    ]),
    "event_type": [
        "market_liquidity_crisis",
        "government_financing_request",
    ]
})




sutff_that_works = pls_work[[
    "period_end",
    "filing_date",
    "fiscal_year",
    "total_debt",
    "ordinary_shares"
]].copy()

sutff_that_works["ticker"] = "F"
sutff_that_works["company_id"] = 2
sutff_that_works["total_assets"] = equity_val

results = results.merge(
    sutff_that_works,
    left_on=[
        "company_id",
        "financial_period_end",
        "financial_filing_date"
    ],
    right_on=[
        "company_id",
        "period_end",
        "filing_date"
    ],
    how="left"
)


testing_the_test = WasMertonRight(results, distress_events)
testing_the_test.create_labels(horizon_days = 22)

print(testing_the_test.calculate_auc())
print(testing_the_test.compare_debt_to_assets())

testing_the_test.compare_debt_to_assets()

plot_data = testing_the_test.results.sort_values("date").copy()

fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(
    plot_data["date"],
    plot_data["distance_to_default"],
    label="Merton Distance to Default",
    color="blue"
)

ax1.set_ylabel("Distance to Default")
ax1.set_xlabel("Date")

ax2 = ax1.twinx()

ax2.plot(
    plot_data["date"],
    plot_data["debt_to_assets"],
    label="Debt / Market Equity",
    color="red"
)

ax2.set_ylabel("Debt / Market Equity")

plt.title("Ford: Merton DtD vs Debt / Market Equity")
plt.show()