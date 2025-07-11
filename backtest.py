from pairsplus import data_io, pairs, signals, portfolio

def main():
    df = data_io.fetch_bars()
    best_pairs = pairs.find_cointegrated(df)
    results = []
    for _, a, b in best_pairs:
        sig = signals.signal_from_spread(df[[a, b]], a, b)
        if sig:
            pnl = portfolio.sim_backtest(df[[a, b]], sig)
            results.append((a, b, pnl))
    print(sorted(results, key=lambda x: x[2], reverse=True))

if __name__ == "__main__":
    main()
