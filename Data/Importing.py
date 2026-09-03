import yfinance as yf
import math
import pandas as pd

from Data.Database import Company, Financials, MarketData
from sqlalchemy.dialects.sqlite import insert
from edgar import Company as edgar_company, set_identity


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

# No batch inserts yet, as i have not run into any problems yet ( we only get 1 report a year, 
# would need 10000 years to make us exceed the row limit in a single  import).


# yfinance does not have much historical data for debts and such, so we
# will need SEC data. Turns out there is a library called edgar tools 
# that will be useful. 

# From reading an SEC filing 2025 10-k Alphabet splits debt into long/short
# term and essentialy only has commercial paper as the short term. Short-term
# debt is essentially the portion of long-term debt due to be settled
# within 1 year

def import_fin_data(ticker,start_year, end_year):

    results = []
    # SEC needs to know who we are to access their data
    set_identity("Andrew Allen andrewlukeallen@email.com")


    company = edgar_company(ticker)
    facts = company.get_facts()
    all_facts = facts.get_all_facts()

    # What we actually want 
    concepts = {
        "assets": "us-gaap:Assets",
        "current": "us-gaap:LongTermDebtCurrent",
        "longterm": "us-gaap:LongTermDebtNoncurrent",
        "shares" : "us-gaap:CommonStockSharesOutstanding"
    }

    for fact in all_facts:

        # Ensure we only get stuff in the year we want
        if fact.concept not in concepts.values():
            continue
        if fact.fiscal_year is None:
            continue
        if not (start_year <= fact.fiscal_year <= end_year):
            continue
        if fact.fiscal_period not in ["Q1", "Q2", "Q3", "FY"]:
            continue

        # Get the stuff we want
        if fact.concept == concepts["assets"]:
            v = "assets"
        elif fact.concept == concepts["current"]:
            v = "current"
        elif fact.concept == concepts["longterm"]:
            v = "longterm"
        elif fact.concept == concepts["shares"]:
            v = "shares"

        else:
            continue

        results.append({
            "ticker": ticker,
            "period_end": fact.period_end,
            "filing_date": fact.filing_date,
            "fiscal_year": fact.fiscal_year,
            "fiscal_period": fact.fiscal_period,
            "concept": v,
            "value": fact.numeric_value,
        })

    return pd.DataFrame(results)

def store_fin_data(data,ticker,session,alpha = 1):

    company = session.query(Company).filter_by(ticker=ticker).first()
    if company is None:
        print(f"{ticker} not found in company database.")
        return

    # Dates threw an error once so we check them
    data["period_end"] = pd.to_datetime(data["period_end"])
    data["filing_date"] = pd.to_datetime(data["filing_date"])
    
    # Convert long to wide
    financials = (
        data.pivot_table(
            index=[
                "ticker",
                "period_end",
                "filing_date",
                "fiscal_year",
                "fiscal_period"
            ],
            columns="concept",
            values="value",
            aggfunc="last"
        )
        .reset_index()
    )

    # Total debt = current portion + alpha * long-term portion (if its not immediately due who really cares)
    financials["total_debt"] = financials["current"].fillna(0) + alpha * financials["longterm"].fillna(0)

    # Rename columns to match database
    financials = financials.rename(columns={
        "assets": "total_assets",
        "shares": "ordinary_shares"
    })

    records = []

    for _, record in financials.iterrows():

        records.append({
            "company_id": company.company_id,
            "filing_date": record["filing_date"],
            "fiscal_year": int(record["fiscal_year"]),
            "fiscal_period": record["fiscal_period"],
            "total_assets": record.get("total_assets"),
            "total_debt": record.get("total_debt"),
            "ordinary_shares": record.get("ordinary_shares"),
            "period_end" : record.get("period_end")
        })

    if not records:
        print(f"{ticker}: no financial records to store.")
        return

    stmt = insert(Financials).values(records)

    stmt = stmt.on_conflict_do_update(
        index_elements=[
            "company_id",
            "period_end",
            "filing_date"
        ],
        set_={
            "total_assets": stmt.excluded.total_assets,
            "total_debt": stmt.excluded.total_debt,
            "ordinary_shares": stmt.excluded.ordinary_shares,
            "fiscal_year": stmt.excluded.fiscal_year,
            "fiscal_period": stmt.excluded.fiscal_period,
        }
    )

    session.execute(stmt)
    session.commit()

    print(
        f"{ticker}: "
        f"{len(records)} financial records stored"
    )

