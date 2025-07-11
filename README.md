# 🟢 PairsPlus Bot

A Python trading bot for pairs trading using cointegration. Supports backtesting and live trading with Alpaca's paper trading API.

---

## 📜 Features
- Cointegration analysis to find mean-reverting pairs
- Rolling z-score signal engine
- Backtesting CLI
- Live trading loop with Alpaca execution
- Modular and testable design

---

## 🗂️ Project Structure

pairsplus-bot/
│
├── pairsplus/
│ ├── config.py
│ ├── data_io.py
│ ├── pairs.py
│ ├── signals.py
│ ├── execution.py
│ └── portfolio.py
│
├── backtest.py
├── trade_live.py
├── requirements.txt
└── README.md


---

## ⚙️ Setup

1️⃣ Clone the repo
```bash
git clone <your-repo-url>
cd pairsplus-bot

2️⃣ Create a virtual environment

python -m venv .venv
source .venv/bin/activate

3️⃣ Install dependencies

pip install -r requirements.txt

4️⃣ Set your Alpaca keys in a .env file:

ALPACA_KEY="your-alpaca-key"
ALPACA_SECRET="your-alpaca-secret"

🧭 Architecture Diagram

+------------------+
|  data_io.py      | <- loads historical bars
+------------------+
        |
        v
+------------------+
|  pairs.py        | <- finds cointegrated pairs
+------------------+
        |
        v
+------------------+
|  signals.py      | <- generates z-score signals
+------------------+
        |
        v
+------------------+
|  execution.py    | <- places trades via Alpaca
+------------------+
        |
        v
+------------------+
|  portfolio.py    | <- (future) manage positions
+------------------+

🚀 Usage
🔎 Backtesting

Run the CLI to evaluate historical pairs:

python backtest.py

    Loads recent Yahoo Finance data

    Finds cointegrated pairs

    Generates signals

    Outputs pairs and simulated PnL

📈 Live Trading

Run live loop (for paper trading) with Alpaca:

python trade_live.py

    Fetches hourly bars

    Finds cointegrated pairs

    Checks for trading signals

    Places paired trades on Alpaca

✅ Testing

Run tests with:

pytest

Lint the code:

ruff .

⚡ Example .env

ALPACA_KEY="your-alpaca-key-here"
ALPACA_SECRET="your-alpaca-secret-here"

🛠️ Future Ideas

    Position sizing and risk limits

    Portfolio-level PnL tracking

    Slippage & commission modeling in backtest

    Database integration for trades and logs

    Advanced execution logic (limit orders, partial fills)

📜 License

MIT License. Use at your own risk.


---

**Instructions for you:**

✅ 1. Open `README.md` in your project root  
✅ 2. Delete anything old in there  
✅ 3. Paste this entire block exactly as is  

---



