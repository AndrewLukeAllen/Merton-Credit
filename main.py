import pandas as pd
import numpy as np
import yfinance as yf

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
    store_fin_data
)

from merton_model import MertonModel
from backtesting import MertonBacktester

from sqlalchemy import select

# Constants
TICKER = "GOOG"
START_DATE = "2020-01-01"
END_DATE = "2025-12-31"


create_tables()

# google = Company(
#     ticker="GOOG",
#     sector="Technology",
#     company_name="Alphabet Inc."
# )

# session.add(google)
# session.commit()

# # Download Share data
# prices = download_share_data(TICKER,START_DATE,END_DATE)
# store_share_data(prices,session)

# # Download Finnancial Data
# fin_data = import_fin_data(TICKER,2020,2025)
# store_fin_data(fin_data,TICKER,session)

# Test if this all plays nice with the Merton Model

stmt = select(Financials.ordinary_shares).where(Financials.company_id == 1)
shares = session.scalars(stmt).all()

stmt = select(MarketData.close, MarketData.date).where(MarketData.company_id == 1)
price = pd.read_sql(stmt,session.bind,columns=["close", "date"])

stmt = select(Financials.total_debt).where(Financials.company_id == 1)
debt = session.scalars(stmt).all()

equity_val = shares[-1] * price["close"].iloc[-1]
m = MertonModel(equity_val,price,debt[-1],1)
results = m.run()

# print(results)



# We now test the backtester ha

stmt = select(MarketData.close,MarketData.date).where(MarketData.company_id == 1).order_by(MarketData.date)
price = pd.read_sql(stmt, session.bind)

stmt = (
    select(
        Financials.filing_date,
        Financials.period_end,
        Financials.total_debt,
        Financials.ordinary_shares
    )
    .where(Financials.company_id == 1)
    .order_by(Financials.filing_date)
)

financials = pd.read_sql(stmt, session.bind)

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
