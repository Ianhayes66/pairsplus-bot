def sim_backtest(df, signal):
    # Example logic:
    spread = df.iloc[:, 0] - df.iloc[:, 1]
    if signal['action'] == "LONG_SPREAD":
        pnl = spread.diff().sum() * 1  # Simulate long spread
    elif signal['action'] == "SHORT_SPREAD":
        pnl = -spread.diff().sum() * 1
    else:
        pnl = 0
    return pnl
