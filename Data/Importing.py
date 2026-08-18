import yfinance as yf
import math

from Data.Database import Company, Financials, MarketData
from sqlalchemy.dialects.sqlite import insert

# I have tried adding session as a variable for these functions after thinking I could have multiple
# active sessions. I never do, just think it'd be fun if i did.


def download_share_data(tickers, start, end):

    # Download Share data

    prices = yf.download(tickers, start=start, end=end)

    # Store in our database

    prices = (
        prices.stack(level= 1, future_stack= True)
        .reset_index()
        .rename(columns={
            "Ticker": "ticker",
            "Date": "date",
            "Close": "close",
        })
    )

    return prices

def store_share_data(data,session):

    batch_size = 10000 

    for ticker in data["ticker"].unique():

        # Check we have a company to import to

        company = session.query(Company).filter_by(ticker = ticker).first()

        if company is None:
            print(f"{ticker} not found in company db.")

        company_data = data[data["ticker"] == ticker]

        records = [
            {
                "company_id": company.company_id,
                "date": row["date"].date(),
                "close": row["close"],
            }
            for __, row in company_data.iterrows()
        ]

        batch_count = 0

        for start in range(0, len(records), batch_size):

            batch = records[start:start + batch_size]

            if not batch:
                continue

            batch = records[start:start + batch_size]

            stmt = insert(MarketData).values(batch)

            stmt = stmt.on_conflict_do_update(
                index_elements=["company_id", "date"],
                set_={
                    "close": stmt.excluded.close,
                }
            )

            session.execute(stmt)
            batch_count += 1
            print(f"batch {batch_count}/{math.ceil(len(data)/batch_size)} complete")
        
            session.commit()   

def download_fin_data(ticker):

    fin = yf.Ticker(ticker).balance_sheet

    records = []

    needed = [
        "Total Assets",
        "Total Debt",
        "Cash Cash Equivalents And Short Term Investments",
    ]
    
    for date in fin.columns:

        # Skip dates where required data is missing
        if any(
            field not in fin.index
            or fin.loc[field, date] != fin.loc[field, date]
            for field in needed
        ):
            print(f"Skipping {ticker} {date.date()}: missing financial data")
            continue

        record = {
            "date": date.date(),

            "total_assets": fin.loc["Total Assets", date],

            "total_debt": fin.loc["Total Debt", date],

            "cash": fin.loc["Cash Cash Equivalents And Short Term Investments", date],
        }

        records.append(record)

    return records

def store_fin_data(data, ticker, session):

    company = session.query(Company).filter_by(ticker=ticker).first()

    if company is None:
        print(f"{ticker} not found in company database.")
        return

    records = [
        {
            "company_id": company.company_id,
            "date": record["date"],
            "total_assets": record["total_assets"],
            "total_debt": record["total_debt"],
            "cash": record["cash"],
        }
        for record in data
    ]

    stmt = insert(Financials).values(records)

    stmt = stmt.on_conflict_do_update(
        index_elements=["company_id", "date"],
        set_={
            "total_assets": stmt.excluded.total_assets,
            "total_debt": stmt.excluded.total_debt,
            "cash": stmt.excluded.cash,
        }
    )

    session.execute(stmt)
    session.commit()

    print(
        f"{ticker}: "
        f"{len(records)} financial records stored"
    )



