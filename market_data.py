import yfinance as yf


def get_stock_snapshot(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")

        if hist.empty:
            return None

        last_close = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last_close
        last_volume = int(hist["Volume"].iloc[-1])

        avg_volume = int(hist["Volume"].tail(5).mean()) if len(hist) >= 1 else last_volume

        price_change_pct = 0
        if prev_close != 0:
            price_change_pct = ((last_close - prev_close) / prev_close) * 100

        volume_ratio = 0
        if avg_volume != 0:
            volume_ratio = last_volume / avg_volume

        return {
            "ticker": ticker,
            "last_close": round(last_close, 2),
            "price_change_pct": round(price_change_pct, 2),
            "last_volume": last_volume,
            "avg_volume_5d": avg_volume,
            "volume_ratio": round(volume_ratio, 2)
        }

    except Exception:
        return None


def get_many_stock_snapshots(ticker_list):
    results = []

    for ticker in ticker_list:
        data = get_stock_snapshot(ticker)
        if data is not None:
            results.append(data)

    return results


def normalize_chart_range(chart_range):
    mapping = {
        "5d": ("5d", "1h"),
        "1mo": ("1mo", "1d"),
        "3mo": ("3mo", "1d"),
        "6mo": ("6mo", "1d"),
        "1y": ("1y", "1wk")
    }
    return mapping.get(chart_range, ("3mo", "1d"))


def get_stock_chart_data(ticker, chart_range="3mo"):
    try:
        period, interval = normalize_chart_range(chart_range)

        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            return None

        points = []

        for idx, row in hist.iterrows():
            try:
                dt = idx.to_pydatetime()
            except Exception:
                dt = idx

            points.append({
                "time": int(dt.timestamp()),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else 0
            })

        return {
            "ticker": ticker,
            "range": chart_range,
            "period": period,
            "interval": interval,
            "points": points
        }

    except Exception:
        return None