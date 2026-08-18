import pandas as pd
import numpy as np

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
    download_fin_data
)

from merton_model import MertonModel

create_tables()

google = Company(
    ticker="GOOG",
    sector="Technology",
    company_name="Alphabet Inc."
)

session.add(google)
session.commit()

# toy inputs work

# #####################################
test = download_share_data(
    "GOOG",
    "2020-01-01",
    "2020-06-01"
)

store_share_data(test, session)

rows = session.query(MarketData).all()

print(f"Number of rows: {len(rows)}")

for row in rows[:5]:
    print(
        row.company.ticker,
        row.date,
        row.close
    )

# toy inputs work


# #####################################
financials = download_fin_data("GOOG")

store_fin_data(financials, "GOOG",session)

rows = session.query(Financials).all()

print(f"Financial rows: {len(rows)}")

for row in rows:
    print(
        row.company.ticker,
        row.date,
        row.total_assets,
        row.total_debt,
        row.cash
    )

# toy inputs work

#########################################


# model = MertonModel(
#     equity_value=2_000_000_000_000,
#     equity_volatility=0.30,
#     debt=60_000_000_000,
#     risk_free_rate=0.04,
#     maturity=1
# )

# result = model.run()

# print(result)

# toy inputs work

#########################################
# A less toy example

company = (
    session.query(Company)
    .filter_by(ticker="GOOG")
    .first()
)

market_data = (
    session.query(MarketData)
    .filter_by(company_id=company.company_id)
    .order_by(MarketData.date)
    .all()
)

prices = pd.DataFrame([
    {
        "date": row.date,
        "close": row.close
    }
    for row in market_data
])


prices["return"] = np.log(
    prices["close"] /
    prices["close"].shift(1)
)

equity_volatility = (
    prices["return"].std() *
    np.sqrt(252)
)



financial = (
    session.query(Financials)
    .filter_by(company_id=company.company_id)
    .order_by(Financials.date.desc())
    .first()
)

latest_price = prices.iloc[-1]["close"]

equity_value = (
    latest_price *
    financial.ordinary_shares
)


# -------------------------
# Merton
# -------------------------

model = MertonModel(
    equity_value=equity_value,
    equity_volatility=equity_volatility,
    debt=financial.total_debt,
    risk_free_rate=0.04,
    maturity=1
)

result = model.run()

print(result)


