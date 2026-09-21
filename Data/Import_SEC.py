# pre 2010 data has no xbrl file or something, so we need
# to automate the extraction of the debt data that we want.

# Some comments on how it went. Originally attempted to parse
# entire html which failed.
# Attempted to parse as text then convert to pd
# Searched HTML for keywords to isolate desired
# cleaned HTML then put into pd

# This is not a very flexible solution
# if we tried to adapt it to say lehman brothers
# Will think on some improvements that could make it possible.


import pandas as pd
from edgar import Company, set_identity
from bs4 import BeautifulSoup

# Cleans input so we keep it in a callable df

def clean_balance_sheet(df):

    # Get dates
    # As sometimes it is not in the first row we need to search a little
    dates = []
    date_cols = []
    for col in df.columns:
        for row in range(min(3, len(df))):
            date = pd.to_datetime(df.loc[row, col], errors="coerce")
            if pd.notna(date):
                date_cols.append(col)
                dates.append(date.strftime("%Y-%m-%d"))

    # Find the row containing two known financial values
    cash_row = df[df[0].astype(str).str.strip() == "Cash and cash equivalents"].iloc[0]

    # Find columns containing the two values
    value_cols = [
        i for i, x in enumerate(cash_row)
        if pd.notna(x) and str(x).replace(",", "").strip().isdigit()
    ]

    # Keep description + those exact columns
    df = df.iloc[:, [0] + value_cols]

    df.columns = ["Description"] + dates
    # Get rid of leftover dates and an unaudited comment
    idx = df[df["Description"].str.strip().eq("ASSETS")].index[0]
    df = df.loc[idx:].reset_index(drop=True)

    return df


def import_total_debt_SEC(company_id,start,end):
    results = []
    year_range = range(start,end+1)
    set_identity("Andrew Allen andrewlukeallen@email.com")

    company = Company(company_id)

    filings = company.get_filings(
        form="10-Q",
        year=year_range
    )

    for filing in filings:


        print("=" * 80)
        print("Processing filing")
        print("=" * 80)
        print(filing.filing_date)

        html_content = filing.html()

        soup = BeautifulSoup(html_content, "lxml")

        # Find the Ford Sector Balance Sheet


        my_table = None

        # Terms that seem to work to find the right table

        required_terms = [
            "AUTOMOTIVE",
            "FINANCIAL SERVICES",
            "TOTAL AUTOMOTIVE ASSETS",
            "TOTAL FINANCIAL SERVICES ASSETS",
            "TOTAL LIABILITIES AND STOCKHOLDERS",
            "DEBT"
        ]

        for table in soup.find_all("table"):

            table_text = " ".join(
                table.get_text(" ", strip=True).split()
            ).upper()

            if all(term in table_text for term in required_terms):
                my_table = table
                break

        if my_table is None:
            print("Could not find Sector Balance Sheet")
            continue

        print("Sector Balance Sheet found!")

        # Extract rows manually


        rows = []

        for tr in my_table.find_all("tr"):

            cells = tr.find_all(["td", "th"])

            if not cells:
                continue

            row = []

            for cell in cells:

                # Get ONLY the text inside the cell
                value = cell.get_text(" ", strip=True)

                # Normalize whitespace
                value = " ".join(value.split())

                row.append(value)

            rows.append(row)


        # Remove completely empty rows


        rows = [
            row for row in rows
            if any(cell.strip() for cell in row)
        ]

        # Make all rows the same length


        max_columns = max(len(row) for row in rows)

        rows = [
            row + [""] * (max_columns - len(row))
            for row in rows
        ]

        # Create DataFrame

        df = pd.DataFrame(rows)

        # Remove completely empty columns
        df = df.loc[:, (df != "").any(axis=0)]

        # Remove completely empty rows
        df = df.loc[(df != "").any(axis=1)]

        # Reset index
        df = df.reset_index(drop=True)

        # Combine split negative numbers

        for col in df.columns:

            for i in range(len(df)):

                value = df.at[i, col]

                if value == "":
                    continue

                # Convert "(1,438" + ")" type situations later
                if value.startswith("(") and not value.endswith(")"):
                    # Leave for now; closing parenthesis may be next cell
                    pass

        # Print ONLY the DataFrame

        # Cleans inputs so we have int (actually float cause thats what the db takes) data to work with

        cleand_df = clean_balance_sheet(df)
        for col in cleand_df.columns[1:]:
            cleand_df[col] = pd.to_numeric(
                cleand_df[col].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("(", "-", regex=False)
                .str.replace(")", "", regex=False)
                .replace("—", pd.NA),
                errors="coerce"
            )

        # We now need to add these important filings into the df we actually export

        # This importinng is imperfect, normally i would attatch fiscal_period
        # but it is marginally more effort than it is worth ATM.

        # The allocation of short/long term debt is to the best of my knowledge

        short_term_debt = cleand_df.loc[cleand_df["Description"].str.strip() == "Debt payable within one year"].iloc[0, 1]

        # I really shouldn';t include ford finnaicals debt in this model
        # long_term_debt = (
        #     cleand_df.loc[cleand_df["Description"].str.strip() == "Debt"].iloc[0, 1]
        #     +
        #     cleand_df.loc[cleand_df["Description"].str.strip() == "Long-term debt"].iloc[0, 1])

        long_term_debt = cleand_df.loc[cleand_df["Description"].str.strip() == "Long-term debt"].iloc[0, 1]


        # Share stuff 
        common_shares = cleand_df.loc[
        cleand_df["Description"].str.contains("Common Stock", case=False, na=False),
            "Description"
        ].iloc[0]

        class_b_shares = cleand_df.loc[
            cleand_df["Description"].str.contains("Class B Stock", case=False, na=False),
            "Description"
        ].iloc[0]

        common_shares = float(
            common_shares.split("(")[1].split("million")[0].replace(",", "").strip()
        )

        class_b_shares = float(
            class_b_shares.split("(")[1].split("million")[0].replace(",", "").strip()
        )

        # Note that technically class b shares are not ordinary shares. will fix later 
        results.append({
            "ticker": "F",
            "period_end": cleand_df.columns[1],
            "filing_date": filing.filing_date,
            "fiscal_year": pd.to_datetime(cleand_df.columns[1]).year,
            "total_debt": (short_term_debt + long_term_debt ) * 1e6,
            "ordinary_shares": (common_shares + class_b_shares) * 1e6,
        })

    return pd.DataFrame(results)