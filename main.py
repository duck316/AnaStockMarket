from flask import Flask, render_template, request
import pandas as pd
import re
import os

app = Flask(__name__)

ranking= 0

def clean_numeric(value):
    """Convierte valores tipo $1.2B, 15%, 12-18 a float"""
    if pd.isna(value):
        return None

    value = str(value)

    # Market Cap: B / M
    if "B" in value:
        return float(value.replace("B", "")) * 1_000
    if "M" in value:
        return float(value.replace("M", ""))

    # Percent
    value = value.replace("%", "")

    # 52-week range
    if "," in value:
        low, high = value.split(",")
        return float(high) - float(low)

    # Remove symbols
    value = re.sub(r"[^\d.-]", "", value)

    try:
        return float(value)
    except:
        return None


@app.route("/", methods=["GET", "POST"])
def AnaMarket():
    table = None
    top = None

    if request.method == "POST":
        file = request.files.get("file")

        if file and file.filename.endswith(".csv"):
            df = pd.read_csv(file)

            columns = [
                "Market Cap",
                "P/E ratio",
                "PEP-Share",
                "Yield",
                "52-week-range"
            ]

            # Limpiar columnas
            for col in columns:
                if col in df.columns:
                    df[col + "_num"] = df[col].apply(clean_numeric)

            # Normalización
            df["Score"] = (
                df["Market Cap_num"].rank(pct=True) +
                df["Yield_num"].rank(pct=True) +
                df["PEP-Share_num"].rank(pct=True) -
                df["P/E ratio_num"].rank(pct=True)
               ## df["52-week-range_num"].rank(pct=True)
            )

            # Ordenar de mejor a mayor
            df = df.sort_values("Score", ascending=False)

            # Ranking Numerico
            df["Ranking"] = range(1, len(df) + 1)

            display_cols = [
                "Ranking",
                "Symbol",
                "Market Cap",
                "P/E ratio",
                "PEP-Share",
                "Yield",
                "52-week-range-low",
                "52-week-range-high",
                "Symbol Description",
                ## "Score"
            ]

            table = df[display_cols].to_html(
                classes="table table-striped table-hover",
                index=False
            )
        top = df.head(10).copy()

        top["Score_norm"] = (top["Score"] / top["Score"].max()) * 100

        ranking_data = top.to_dict(orient="records")
        return render_template("index.html", table=table, ranking=ranking_data)

    else:
        table = None
        ranking = None
        top = None

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)






