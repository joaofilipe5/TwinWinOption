# Twin-Win Payoff Simulation

An educational Monte Carlo study of a barrier-dependent payoff linked to WTI crude oil futures (`CL=F`). The script simulates geometric price paths, detects upper/lower barrier crossings, and reports the average terminal payoff under its historical-data assumptions.

## Payoff model

The reference dates in `TwinWinPricingFinal.py` are 14 December 2023 and 15 December 2025. Barriers are 140% and 60% of the initial observed price. For a USD 1,000 denomination, a knocked-out path or an absolute terminal variation below 6% receives USD 1,060; other paths receive USD 1,000 multiplied by one plus the absolute variation.

The default simulation allocates 100,000 paths and advances a number of steps based on the calendar-day difference between the reference dates. Historical closing-price log returns supply drift and volatility estimates.

## Setup and execution

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python TwinWinPricingFinal.py --simulations 1000 --seed 42
```

Execution requires Yahoo Finance access. The default remains 100,000 paths and uses substantial memory: the price-path array alone is roughly 560 MiB, with extra memory for barrier arrays. `--simulations` selects a smaller path count; `--seed` makes the random draws reproducible when market inputs remain the same. `--help` explains the command without downloading market data. Importing the module also does not download or simulate automatically.

## Interpretation and limitations

The printed value is an **undiscounted average simulated payoff**, not a validated arbitrage-free option price. The code uses historical estimates rather than a calibrated risk-neutral process, does not discount cash flows, and mixes calendar-day step counts with `dt = 1/252`. Daily return estimates also need consistent time scaling before this can support pricing conclusions. It uses a lognormal model on crude-oil futures and assumes positive observations; that assumption is not universally valid.

There is no confidence interval or convergence study. The seed is optional, so an unseeded run remains random. Closing-price extraction supports flat-column and modern single-ticker DataFrames, and downloads explicitly preserve unadjusted closing prices with `auto_adjust=False`. The original drift, time step, barrier thresholds and payoff formulas are retained; execution repairs do not change their pricing limitations.

## Offline validation

Module import, scalar closing-price extraction, a small seeded simulation and the complete calculation entry point were tested with synthetic historical prices and mocked Yahoo Finance downloads. Repeated seeded calls produced identical finite results. Separate hand-constructed paths exercised the upper barrier, lower barrier, below-6% terminal move and larger terminal move branches of the original payoff rule. No live data was fetched, and no new pricing-accuracy or financial-output claim accompanies these checks.
