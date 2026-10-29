# Call Option Optimization Tool

A Streamlit dashboard for screening listed call options using market data, a Black–Scholes theoretical pricing benchmark, option Greeks, and user-defined filters.

The tool is designed to help explore call-option contracts for further research. It is an analytical screener—not a trading system, investment recommendation, or guarantee of profitability.

## Features

- **Underlying quote:** Retrieves the latest available closing price for a selected ticker.
- **Historical volatility:** Estimates annualized volatility from historical daily log returns (60-day history by default).
- **Options-chain scan:** Examines listed call options with expirations within the next 60 days.
- **Theoretical value:** Calculates a Black–Scholes call value using historical volatility as the volatility input.
- **Greeks:** Calculates call delta, gamma, and daily theta using the option chain's reported implied volatility.
- **Premium-based annualized yield:** Estimates a simple annualized premium-to-share-price ratio.
- **Interactive filters:** Filter by annualized yield, moneyness, valuation status, delta, implied volatility, and theta.
- **Results table:** Displays contracts that pass the selected filters.

## Repository contents

```text
.
├── call_option_tool.py
├── README.md
├── METHODOLOGY.md
└── requirements.txt
```

## Requirements

- Python 3.10 or newer recommended
- Internet access for Yahoo Finance data retrieval
- The packages listed in `requirements.txt`

## Installation

Clone the repository and enter its directory:

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the dashboard

```bash
streamlit run call_option_tool.py
```

Streamlit will print a local URL (typically `http://localhost:8501`) to open in your browser.

## How to use it

1. Enter a stock ticker in the sidebar (the default is `AAPL`).
2. Set the minimum annualized premium yield.
3. Choose whether to show all calls, out-of-the-money (OTM) calls, or in-the-money (ITM) calls.
4. Optionally show only contracts classified as overvalued by the tool's model comparison.
5. Adjust the delta, implied-volatility, and daily-theta filters.
6. Adjust the risk-free rate in **Advanced Environment Settings** if desired.
7. Review the contracts returned in the results table.

If no contracts appear, try widening the filters, checking the ticker, or running the app when market data is available. Yahoo Finance data can be delayed, incomplete, or unavailable.

## Understanding the output

| Field | Meaning |
|---|---|
| Expiration | Contract expiration date |
| Days | Calendar days until expiration |
| Moneyness | ITM or OTM classification based on underlying price and strike |
| Strike | Option strike price |
| Market Price | Midpoint of bid and ask when bid is positive; otherwise last traded price |
| Fair Price (HV) | Black–Scholes call value using estimated historical volatility |
| Variance | Relative difference between selected market premium and model value |
| Annualized Yield | Premium divided by underlying share price, scaled to a 365-day year |
| Market IV | Implied volatility reported in the options chain |
| Delta | Model call delta calculated using market IV |
| Gamma | Model call gamma calculated using market IV |
| Theta (Daily) | Approximate daily time decay calculated using market IV |
| Valuation Status | Overvalued, undervalued, or fair value according to the script's 5% thresholds |

## Important assumptions and limitations

- **Not financial advice.** Outputs are estimates intended for research and education, not personalized investment advice.
- **Yield is not total return.** The annualized-yield metric is not a forecast of profit and does not account for assignment, buybacks, transaction costs, taxes, dividends, or changes in the underlying price.
- **Annualization is simple.** It scales the premium/share-price ratio by `365 / days_to_expiry`; it does not model reinvestment or the probability of repeating the trade.
- **Delta is not exact assignment probability.** Delta is sometimes used as a rough probability proxy under restrictive assumptions, but it is not the same as the real-world probability of assignment.
- **Theoretical price depends on assumptions.** The Black–Scholes model does not fully represent early exercise, discrete dividends, bid–ask spreads, liquidity, or all market dynamics.
- **Historical volatility is not implied volatility.** The model compares a price computed with historical volatility to a market premium. That comparison is a heuristic, not proof that an option is mispriced.
- **Market data quality matters.** The code uses Yahoo Finance through `yfinance`; quotes and option-chain fields may be stale, missing, delayed, or inconsistent.
- **Contract filters are screening rules.** A contract passing the filters is not necessarily suitable for a particular portfolio or strategy.

See [`METHODOLOGY.md`](METHODOLOGY.md) for formulas, implementation details, and further caveats.

## Data provider

Market data is retrieved through [`yfinance`](https://github.com/ranaroussi/yfinance), which accesses Yahoo Finance data. Review the provider's terms and ensure your use complies with applicable terms and restrictions.

## Disclaimer

This project is provided “as is,” without warranties of any kind. It is not investment, legal, tax, or accounting advice. Options involve substantial risk and may not be appropriate for every investor. Verify data and calculations independently before making any financial decision.

## Possible future improvements

- Add tests for pricing, Greeks, filters, and edge cases.
- Use dividend-aware pricing for dividend-paying equities.
- Improve quote handling with bid–ask midpoint validation and liquidity checks.
- Make yield definitions strategy-specific (for example, covered-call return based on share cost basis).
- Clarify that delta is a heuristic rather than an assignment probability.
- Add explicit timestamps, data freshness indicators, and caching.
