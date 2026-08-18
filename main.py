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


create_tables()


google = Company(
    ticker="GOOG",
    sector="Technology",
    company_name="Alphabet Inc."
)

session.add(google)
session.commit()


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