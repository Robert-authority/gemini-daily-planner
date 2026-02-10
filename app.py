from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime, timedelta

app = Flask(__name__)

# ====== SECRET SESSION KEY ======
# Biar login session aman
app.secret_key = "super_secret_key_change_this_later"

# ====== LOAD ENV ======
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not GEMINI_API_KEY:
    raise ValueError("API Key Gemini tidak ditemukan! Pastikan ada di file .env")

if not APP_PASSWORD:
    raise ValueError("APP_PASSWORD tidak ditemukan! Pastikan ada di file .env")

genai.configure(api_key=GEMINI_API_KEY)

# Model yang tersedia di list kamu
model = genai.GenerativeModel("models/gemini-2.5-flash")


# ====== DATABASE ======
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jadwal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT,
            tanggal TEXT,
            jam TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ====== AUTH ======
def is_logged_in():
    return session.get("logged_in") == True


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "")

        if pw == APP_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Password salah 😭")

    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ====== ROUTES ======
@app.route("/")
def index():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/add", methods=["POST"])
def add_jadwal():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    user_text = request.json.get("text", "").strip()
    if not user_text:
        return jsonify({"status": "error", "message": "Teks kosong"}), 400

    today = datetime.now().date()

    prompt = f"""
Kamu adalah asisten pencatat jadwal.

Ubah teks user menjadi JSON list.
Output HARUS JSON saja, tanpa penjelasan, tanpa markdown.

Format:
[
  {{
    "judul": "...",
    "hari": "today/tomorrow/date",
    "tanggal": "",
    "jam": "HH:MM"
  }}
]

Aturan:
- Jika user bilang "hari ini", isi hari="today"
- Jika user bilang "besok", isi hari="tomorrow"
- Jika user menyebut tanggal jelas (contoh 12 februari 2026), isi hari="date" dan isi tanggal "YYYY-MM-DD"
- Jika user tidak menyebut jam, isi "00:00"
- Judul singkat, jangan pakai kata "jam", jangan pakai kata "besok"

Teks user:
{user_text}
"""

    try:
        response = model.generate_content(prompt)
        jadwal_json = response.text.strip()

        # Bersihin kalau AI ngasih ```json
        jadwal_json = jadwal_json.replace("```json", "").replace("```", "").strip()

        data = json.loads(jadwal_json)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        for item in data:
            hari = item.get("hari", "today")
            jam = item.get("jam", "00:00")
            judul = item.get("judul", "Tanpa Judul")

            # Tentuin tanggal final sesuai waktu sekarang
            if hari == "today":
                tanggal_final = str(today)
            elif hari == "tomorrow":
                tanggal_final = str(today + timedelta(days=1))
            elif hari == "date":
                tanggal_final = item.get("tanggal", str(today))
            else:
                tanggal_final = str(today)

            c.execute(
                "INSERT INTO jadwal (judul, tanggal, jam) VALUES (?, ?, ?)",
                (judul, tanggal_final, jam)
            )

        conn.commit()
        conn.close()

        return jsonify({"status": "success", "data": data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/jadwal", methods=["GET"])
def get_jadwal():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, judul, tanggal, jam FROM jadwal ORDER BY tanggal, jam")
    rows = c.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "judul": r[1],
            "tanggal": r[2],
            "jam": r[3]
        })

    return jsonify(result)


@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_jadwal(id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM jadwal WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    # host 0.0.0.0 biar bisa diakses lewat ngrok
    app.run(host="0.0.0.0", port=5000, debug=True)
