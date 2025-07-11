import schedule
import time
from pairsplus import data_io, pairs, signals, execution

def job():
    df = data_io.fetch_bars(interval="1h", lookback=90)
    best_pairs = pairs.find_cointegrated(df, max_pairs=5)
    for _, a, b in best_pairs:
        sig = signals.signal_from_spread(df[[a, b]], a, b)
        if sig and sig["action"] == "LONG_SPREAD":
            execution.place_pair_trade(a, b)
        elif sig and sig["action"] == "SHORT_SPREAD":
            execution.place_pair_trade(b, a)

schedule.every().hour.at(":05").do(job)

while True:
    schedule.run_pending()
    time.sleep(30)
