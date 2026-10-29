# Methodology: Call Option Optimization Tool

## 1. Purpose and scope

This document describes the calculations and screening logic implemented in `call_option_tool.py`. The application retrieves stock and listed-option data, estimates historical volatility, calculates Black–Scholes call values and selected Greeks, and filters contracts according to sidebar inputs.

The results are intended for exploratory analysis. The script does not determine whether a trade is suitable for a user, optimize a portfolio, or estimate a complete probability distribution of investment outcomes.

## 2. Data inputs

The application uses `yfinance` to retrieve:

- The selected ticker's latest available daily closing price (`history(period="1d")`).
- Historical daily closing prices over a default `60d` period.
- Listed option expiration dates and call-option chain fields, including strike, bid, ask, last price, and implied volatility.

Only expiration dates with more than zero and no more than 60 calendar days remaining are scanned. The script skips a contract when the selected premium is at or below `$0.05`.

Data availability, freshness, and completeness depend on the upstream source. The script does not independently verify exchange quotes or guarantee real-time data.

## 3. Historical volatility

Let \(S_t\) be the closing price on day \(t\). The script calculates daily log returns:

\[
r_t = \ln\left(\frac{S_t}{S_{t-1}}\right)
\]

It takes the sample standard deviation of those daily log returns, \(s_r\), and annualizes it using 252 trading days:

\[
\sigma_{\mathrm{HV}} = s_r\sqrt{252}
\]

This estimate is used as the volatility input for the theoretical call-price benchmark. If fewer than 10 historical rows are returned, the code uses a fallback volatility of `0.30` (30%).

Historical volatility measures realized past price variability. It is not a forecast and can differ materially from the market's implied volatility.

## 4. Black–Scholes call valuation

The code uses the European-call Black–Scholes formula, with no dividend yield term:

\[
d_1 = \frac{\ln(S/K)+(r+\frac{1}{2}\sigma^2)T}{\sigma\sqrt{T}}
\]

\[
d_2 = d_1-\sigma\sqrt{T}
\]

\[
C = S\,N(d_1)-K e^{-rT}N(d_2)
\]

Where:

- \(S\): underlying share price
- \(K\): strike price
- \(T\): time to expiration in years (`days_to_expiry / 365`)
- \(r\): user-configurable continuously compounded risk-free rate (default `0.045`)
- \(\sigma\): volatility input
- \(N(\cdot)\): standard normal cumulative distribution function
- \(C\): theoretical call value

For the displayed **Fair Price (HV)**, the code uses historical volatility. If the input volatility is nonpositive, it substitutes `0.001`. If time to expiration is nonpositive, the function returns intrinsic value and simplified Greeks.

**Interpretation:** “Fair Price (HV)” is a model output under these assumptions, not an objectively established fair value. The implementation does not include a dividend yield, and the standard Black–Scholes model assumes European exercise. Listed equity options may be American-style and dividend payments can matter.

## 5. Market premium selection

For each call contract, the script selects the premium as follows:

1. If the bid is greater than zero, use the midpoint: \((\mathrm{bid}+\mathrm{ask})/2\).
2. Otherwise, use `lastPrice`.

It then skips the contract if the selected premium is less than or equal to `$0.05`.

This is a simple rule. It does not check whether the ask is valid, whether the spread is unusually wide, whether the last trade is recent, or whether the market is liquid. Therefore, the selected premium may not represent an executable price.

## 6. Premium-based annualized yield

The code calculates a simple premium-to-share-price percentage:

\[
R_{\mathrm{period}} = \frac{P}{S}\times 100
\]

It then scales that ratio to a 365-day year:

\[
R_{\mathrm{annualized}} = R_{\mathrm{period}}\times\frac{365}{D}
\]

Where \(P\) is the selected option premium, \(S\) is the current underlying share price, and \(D\) is calendar days to expiration.

This metric is labeled **Annualized Yield** in the UI. It is a simple annualized premium ratio, not an expected return, annual percentage yield, or guaranteed income rate. It does not account for strike-specific economics, assignment, losses on the underlying, the cost basis of shares, transaction costs, taxes, dividends, or the ability to repeat the trade at similar prices.

For a covered call, the relevant return calculation depends on the investor's share cost basis and the stock price at assignment or expiration. The script's `premium / current share price` ratio is not a complete covered-call return calculation.

## 7. Greeks

The code calculates delta, gamma, and theta using Black–Scholes, with the option-chain implied volatility as \(\sigma\). The Greeks therefore use a different volatility input from the **Fair Price (HV)** benchmark.

### Delta

For a call:

\[
\Delta = N(d_1)
\]

The dashboard labels the delta filter “Probability of Assignment.” Delta is often used as a rough probability proxy in some contexts, but it is **not the actual probability of assignment**. Assignment depends on exercise and holder behavior, dividends, moneyness, time, and other factors. The slider filters the calculated model delta only.

### Gamma

\[
\Gamma = \frac{\phi(d_1)}{S\sigma\sqrt{T}}
\]

Here, \(\phi(\cdot)\) is the standard normal probability density function. Gamma describes the sensitivity of delta to changes in the underlying price under the model assumptions.

### Theta

The implementation calculates the following call theta expression and divides by 365 to display a daily figure:

\[
\Theta_{\mathrm{daily}} =
\frac{
-\frac{S\phi(d_1)\sigma}{2\sqrt{T}}
-rKe^{-rT}N(d_2)
}{365}
\]

This is a simplified, no-dividend call theta convention. The value is an approximate model sensitivity, not a promise that an option's market value will decline by that amount each calendar day. Theta conventions can differ across systems, and actual option prices also respond to changes in the underlying, implied volatility, rates, dividends, and liquidity.

## 8. Moneyness classification

The code classifies a call as ITM when:

\[
S > K
\]

Otherwise, it classifies the call as OTM. Consequently, a call with \(S = K\) is classified as OTM in this implementation, although it is conventionally described as at-the-money. The UI offers “All,” “Only OTM,” and “Only ITM” options.

## 9. Relative valuation heuristic

The code compares the selected market premium \(P\) with the Black–Scholes theoretical value \(C\) computed using historical volatility:

\[
V = \frac{P-C}{C}
\]

Classification thresholds are:

- **OVERVALUED:** \(V > 0.05\) (market premium more than 5% above model value)
- **UNDERVALUED:** \(V < -0.05\) (market premium more than 5% below model value)
- **FAIR VALUE:** otherwise

When \(C\) is not positive, the code sets the variance to zero. This is a heuristic comparison. It does not establish that a contract is truly overvalued or undervalued, because the market premium and model value may reflect different volatility assumptions, dividend treatment, exercise style, quote quality, and other inputs.

## 10. Screening sequence

For each eligible contract, the script applies the following checks:

1. Annualized yield must be at least the selected minimum.
2. The contract must meet the selected moneyness state.
3. If “Show ONLY Overvalued Contracts” is checked, the contract must be classified as overvalued.
4. Calculated delta must fall within the selected delta range.
5. Market implied volatility (reported IV multiplied by 100) must fall within the selected IV range.
6. Theta must be greater than or equal to the selected maximum-theta-decay threshold.

Only contracts passing all active filters are added to the displayed table.

## 11. Implementation notes and limitations

- **No dividends:** The pricing formula omits dividend yield and discrete dividends.
- **Exercise style:** The model is European-style, while many US equity options are American-style.
- **Quote quality:** Bid/ask midpoint and last price may not be executable or current.
- **Volatility comparison:** Historical volatility is used for the theoretical benchmark; market IV is used for Greeks. The comparison is not like-for-like.
- **Annualization:** The yield metric scales a premium ratio linearly and assumes no compounding or reinvestment.
- **Assignment label:** Delta is a model output, not an assignment probability.
- **Boundary handling:** The implementation does not comprehensively guard against every invalid market input, such as a zero or negative underlying price, missing IV, or an ask below the bid.
- **Theta interpretation:** The displayed daily theta is a model estimate and is sensitive to conventions and inputs.
- **No strategy-level payoff analysis:** The app does not model the full payoff of a covered call, naked call, rolling strategy, or portfolio.
- **No transaction frictions:** Commissions, bid–ask execution costs, taxes, margin requirements, and capital constraints are not included.
- **No recommendation logic:** Passing filters does not imply that a trade should be entered.

## 12. Suggested validation and future work

Potential improvements include:

1. Add unit tests against known Black–Scholes examples and finite-difference checks for Greeks.
2. Add dividend yield and, where appropriate, an American-option model.
3. Validate all market inputs and handle missing or crossed quotes explicitly.
4. Display quote timestamps, spreads, open interest, and volume to help assess liquidity.
5. Rename the delta slider to “Call Delta” and explain its limitations in the UI.
6. Distinguish the simple annualized premium ratio from strategy-specific returns.
7. Add covered-call payoff and breakeven analysis using user-supplied share cost basis.
8. Add automated tests for moneyness boundaries, valuation thresholds, and filter logic.

---
This methodology documents the current implementation and is not a statement that its outputs are accurate forecasts or trading recommendations.
