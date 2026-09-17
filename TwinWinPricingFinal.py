import yfinance as yf
import numpy as np
import pandas as pd
import argparse

# Define the ticker for WTI Crude Oil
ticker = "CL=F"

# Define the key dates
initial_pricing_date = "2023-12-14"
final_pricing_date = "2025-12-15"

# Fetch initial price with error handling
def closing_prices(data, symbol):
    """Return a single closing-price Series for old or modern yfinance output."""
    if 'Close' not in data.columns:
        raise ValueError(f"No closing-price column returned for {symbol}")
    prices = data['Close']
    if isinstance(prices, pd.DataFrame):
        if symbol in prices.columns:
            prices = prices[symbol]
        elif prices.shape[1] == 1:
            prices = prices.iloc[:, 0]
        else:
            raise ValueError(f"Cannot identify closing prices for {symbol}")
    return pd.to_numeric(prices, errors='raise')


def fetch_price(ticker, date, attempts=5):
    for i in range(attempts):
        start_date = pd.to_datetime(date) + pd.Timedelta(days=i)
        end_date = start_date + pd.Timedelta(days=1)
        data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), auto_adjust=False)
        if not data.empty:
            prices = closing_prices(data, ticker).dropna()
            if not prices.empty:
                return float(prices.iloc[0])
    raise ValueError(f"No data found for {ticker} starting from {date} after {attempts} attempts")

# Simulation parameters
num_simulations = 100000
num_days = (pd.to_datetime(final_pricing_date) - pd.to_datetime(initial_pricing_date)).days
dt = 1 / 252  # Assuming 252 trading days in a year

# Simulation function
def simulate_price_paths(initial_price, drift, volatility, dt, num_days, num_simulations, seed=None):
    if num_days < 1 or num_simulations < 1:
        raise ValueError("Simulation days and path count must be positive")
    rng = np.random.default_rng(seed)
    price_paths = np.zeros((num_days, num_simulations))
    price_paths[0] = initial_price
    for t in range(1, num_days):
        rand = rng.standard_normal(num_simulations)
        price_paths[t] = price_paths[t-1] * np.exp(drift * dt + volatility * np.sqrt(dt) * rand)
    return price_paths

def calculate_payoffs(price_paths, initial_price, denomination=1000):
    # Original barrier and terminal-payoff rules are preserved.
    upper_knock_out_price = 1.40 * initial_price
    lower_knock_out_price = 0.60 * initial_price
    knock_out = np.any(
        (price_paths >= upper_knock_out_price) | (price_paths <= lower_knock_out_price),
        axis=0,
    )
    final_prices = price_paths[-1]
    variation = abs(final_prices - initial_price) / initial_price
    return np.where(
        knock_out,
        denomination * 1.06,
        np.where(variation < 0.06, denomination * 1.06, denomination * (1 + variation)),
    )


def main(simulations=num_simulations, seed=None):
    if simulations < 1:
        raise ValueError("The simulation count must be positive")
    initial_price = fetch_price(ticker, initial_pricing_date)
    if not np.isfinite(initial_price) or initial_price <= 0:
        raise ValueError("A finite positive initial price is required")
    print(f"Initial Price on {initial_pricing_date}: ${initial_price:.2f}")

    historical_data = yf.download(ticker, start="1980-01-01", end=initial_pricing_date, auto_adjust=False)
    historical_close = closing_prices(historical_data, ticker)
    log_returns = np.log(historical_close / historical_close.shift(1)).dropna()
    if len(log_returns) < 2 or not np.isfinite(log_returns).all():
        raise ValueError("At least two finite historical log returns are required")
    # Preserve the original daily historical estimates and time scaling.
    drift = float(log_returns.mean() - 0.5 * log_returns.var())
    volatility = float(log_returns.std())
    days = (pd.to_datetime(final_pricing_date) - pd.to_datetime(initial_pricing_date)).days
    price_paths = simulate_price_paths(initial_price, drift, volatility, dt, days, simulations, seed=seed)
    expected_payoff = float(np.mean(calculate_payoffs(price_paths, initial_price)))
    print(f"Expected Payoff: ${expected_payoff:.2f}")
    return expected_payoff


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Educational twin-win payoff simulation")
    parser.add_argument('--simulations', type=int, default=num_simulations, help="Number of Monte Carlo paths (default: 100000)")
    parser.add_argument('--seed', type=int, default=None, help="Optional reproducible random seed")
    args = parser.parse_args()
    if args.simulations < 1:
        parser.error('--simulations must be positive')
    main(simulations=args.simulations, seed=args.seed)
