from flask import Flask, request, jsonify
import pandas as pd
import yfinance as yf

app = Flask(__name__)

# --- Load CSV Watchlist ---
def load_csv(path="watchlist.csv"):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    return df

# --- Scoring function for investment ranking ---
def score_symbol(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Basic scoring example
        score = 0

        # 1. Performance today (% change)
        if "regularMarketChangePercent" in info and info["regularMarketChangePercent"]:
            pct = info["regularMarketChangePercent"]
            score += pct

        # 2. Closer to 52-week high → higher score
        if "fiftyTwoWeekHigh" in info and "regularMarketPrice" in info:
            high = info["fiftyTwoWeekHigh"]
            price = info["regularMarketPrice"]
            if high and price:
                score += (price / high) * 10

        # 3. Volume score
        if "volume" in info:
            volume = info["volume"]
            if volume:
                score += min(volume / 1_000_000, 10)

        return {
            "symbol": symbol,
            "score": round(score, 2),
            "price": info.get("regularMarketPrice", None)
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


# --- Web Route: Home ---
@app.route("/")
def home():
    return jsonify({"message": "Finance Web API funcionando"})


# --- Web Route: Upload CSV ---
@app.route("/upload", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip().str.lower()
    df.to_csv("watchlist.csv", index=False)

    return jsonify({"status": "watchlist cargada", "rows": len(df)})


# --- Web Route: Ranking ---
@app.route("/rank")
def rank_watchlist():
    df = load_csv()

    if "symbol" not in df.columns:
        return jsonify({"error": "CSV necesita columna 'symbol'"})

    symbols = df["symbol"].unique()

    results = [score_symbol(sym) for sym in symbols]
    results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    return jsonify({"ranking": results})


if __name__ == "__main__":
    app.run(debug=True)