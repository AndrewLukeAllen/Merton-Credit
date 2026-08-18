# Motivation
This was somewhat prompted by how a buyer could assess if GOOG current debt raise in Australia
was a good buy, outside of qualitative assesment.

RBA already does this so it seems the motivation is sound.

## What is the Merton model + why did we decide to use it

- Looked up on google "good quant model to determine if a company will ddefault due to debt raise" 
    and Merton seemed the most interesting to implement.
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