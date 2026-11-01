# Options Strategy Simulator — Stage 1

Stage 1 separates the financial formulas from the Tkinter interface and corrects Bull Call Spread handling for debit, zero-debit and credit cases.

## Files
- `main.py`: desktop UI
- `finance_functions.py`: Black–Scholes, payoff and strategy metrics
- `test_finance.py`: formula tests
- `requirements.txt`: dependencies
- `build.bat`: Windows executable build

## Run
```powershell
python -m pip install -r requirements.txt
python main.py
```

## Test formulas
```powershell
python -m unittest -v test_finance.py
```

## Model assumptions
European options; no dividends, brokerage, taxes or slippage. Black–Scholes assumes constant volatility and risk-free rate. Payoffs are at expiry and shown per lot in the UI.
