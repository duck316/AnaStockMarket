from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os

## Carga CSV
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/upload", methods=["POST"])
def upload_csv():
    file = request.files.get("file")

    if not file or not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(path)

    # 🔥 RESPUESTA INMEDIATA
    return jsonify({"status": "ok", "file": filename}), 200

## Procesa y muestra
@app.route("/")
def index():
    return render_template("index.html")

## Procesa CSV Get y Post

@app.route("/analyze/<filename>")
def analyze(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    df = pd.read_csv(path)

    # TODO: tu lógica actual de pandas aquí

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

    table = df.to_html(
        classes="table table-striped table-hover",
        index=False
    )

    top = df.head(10).copy()

    top["Score_norm"] = (top["Score"] / top["Score"].max()) * 100

    ranking_data = top.to_dict(orient="records")
    return render_template("index.html", table=table, ranking=ranking_data)
