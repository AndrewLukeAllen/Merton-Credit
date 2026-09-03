import requests
from datetime import date, timedelta
from edgar import Company, set_identity
import pandas as pd 

set_identity("Andrew Allen andrewlukeallen@email.com")


alphabet  = Company("GOOGL")
facts = alphabet.get_facts()

current = facts.time_series("LongTermDebtCurrent")
longterm = facts.time_series("LongTermDebtNoncurrent")

dates = [
    "2025-03-31",
    "2025-06-30",
    "2025-09-30",
    "2025-12-31"
]

current = current[
    current["period_end"].astype(str).isin(dates)
]

longterm = longterm[
    longterm["period_end"].astype(str).isin(dates)
]

current = current.drop_duplicates(subset=["period_end"])
longterm = longterm.drop_duplicates(subset=["period_end"])

print(current)
print(longterm)

assets = facts.time_series("us-gaap:Assets")
assets_2025 = assets[
    assets["period_end"].astype(str).isin([
        "2025-03-31",
        "2025-06-30",
        "2025-09-30",
        "2025-12-31"
    ])
]

# Keep only the actual 2025 quarter-end observations
quarter_ends = [
    "2025-03-31",
    "2025-06-30",
    "2025-09-30",
    "2025-12-31"
]

all_facts = facts.get_all_facts()

# print(type(all_facts))
# print(len(all_facts))

# print(type(all_facts[0]))
# print(all_facts[0])

# print(dir(all_facts[0]))

def get_quarterly_facts(all_facts, concept, year=2025):
    results = []

    for fact in all_facts:
        if fact.concept != concept:
            continue

        if fact.fiscal_year != year:
            continue

        if fact.fiscal_period not in ["Q1", "Q2", "Q3", "FY"]:
            continue

        results.append({
            "period_end": fact.period_end,
            "filing_date": fact.filing_date,
            "fiscal_period": fact.fiscal_period,
            "fiscal_year": fact.fiscal_year,
            "form_type": fact.form_type,
            "value": fact.numeric_value,
            "accession": fact.accession
        })

    return results

assets = get_quarterly_facts(
    all_facts,
    "us-gaap:Assets"
)

for row in assets:
    print(row)