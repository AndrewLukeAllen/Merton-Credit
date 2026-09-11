# Motivation
This was somewhat prompted by how a buyer could assess if GOOG current debt raise in Australia
was a good buy, outside of qualitative assesment.

RBA already does this so it seems the motivation is sound.

## What is the Merton model + why did we decide to use it

- Looked on google for a way to model credit risk based on equity data, as 
    that was readily available through yfinance and SEC filings. Merton was selected 
    as it seemed like an  interesting extension to the idea of debt to equity ratio.
- Merton prices the equity of a company as a European call and treats debt as the strike price
    it then predict the probability of default as if total assets are < debt the company defaults.

# Goals
- See if I can build a Merton credit risk model that can identify deteriorating companies before default 
    i.e. see if distance to default and modeled implied PD provide that early warning. 
- Test on previously failed / succesful equities i.e. victims of 2008 crash
- Apply framework to Alphabets current debt raise in australia

# Methodology

1. Build the dataset from yfinance and store it using SQLAlchemy
2. Estimate daily/monthly/yearly volatility
3. Define the default point
4. Calibrate Merton model, distance to default (DtD)
5. Convert DtD to PD
6. Test and Benchmark
7. Apply to the Alphabet debt raise (possibly stress test)

I will say the model has been succesful if it can resonably predict that if:
1. deteriorating DtD leads to higher incidence of financial distress
2. It outperforms Debt / Assets

# Progres
1. Done
2. Done (historical, likely will improve to GARCH)
3. Kinda (Currently just use Total debt for simplicity)
4. Done
5. Done (assume PD ~ N(DtD))
6. In progress
    - Added filing date to to manually catch lookahead bias
    - Data for failed companies is annoyingly hard to get
        may use Ford as it still exists but needs some work 
        to reach usable point
7. Done, it is a safe buy
