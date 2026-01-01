from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import re

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def clean_numeric(value):
    if pd.isna(value):
        return None

    value = str(value)
    value = value.replace("%", "")
    value = re.sub(r"[^\d.-]", "", value)

    try:
        return float(value)
    except:
        return None


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", table=None, ranking=None)


@app.route("/uploads", methods=["POST"])
def upload():
    try:
        file = request.files.get("file")

        if not file or not file.filename.endswith(".csv"):
            return jsonify({"error": "Invalid file"}), 400

        df = pd.read_csv(file)

        required_cols = [
            "Market Cap",
            "Yield",
            "PEP-Share",
            "P/E ratio"
        ]

        for col in required_cols:
            if col not in df.columns:
                return jsonify({"error": f"Missing column {col}"}), 400
            df[col + "_num"] = df[col].apply(clean_numeric)

        df["Score"] = (
            df["Market Cap_num"].rank(pct=True) +
            df["Yield_num"].rank(pct=True) +
            df["PEP-Share_num"].rank(pct=True) -
            df["P/E ratio_num"].rank(pct=True)
        )

        df = df.sort_values("Score", ascending=False)
        df["Ranking"] = range(1, len(df) + 1)

        table = df.to_html(
            classes="table table-striped table-hover",
            index=False
        )

        top = df.head(10).copy()
        top["Score_norm"] = (top["Score"] / top["Score"].max()) * 100
        ranking = top.to_dict(orient="records")

        return render_template(
            "index.html",
            table=table,
            ranking=ranking
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
