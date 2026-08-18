from datetime import date
from Data.Database import session, create_tables, Company, Financials

# Initial Test

create_tables()

google = Company(
    ticker="GOOG",
    sector="Technology",
    company_name="Alphabet Inc."
)

financial = Financials(
    date=date(2025, 12, 31),
    total_assets=500_000_000_000,
    long_term_debt=20_000_000_000,
    cash=100_000_000_000
)

google.financials.append(financial)

session.add(google)
session.commit()

print(google.company_id)
print(google.financials)
print(google.financials[0].company)