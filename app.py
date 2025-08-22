from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
from flask_cors import CORS
import sqlite3, os, datetime, hashlib, secrets, re

DB_PATH = os.environ.get("DB_PATH", "codes.db")
BASE_URL = os.environ.get("BASE_URL", "")  # e.g., set to your hosted domain if needed

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# -------- Utilities --------
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS codes (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT NOT NULL,
            pin_hash TEXT,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON codes(created_at)")
    conn.commit()
    conn.close()

def generate_id(length=7):
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def is_valid_id(code_id: str) -> bool:
    return bool(re.fullmatch(r"[0-9A-Za-z_-]{5,16}", code_id))

# Basic naive rate limiting (per-IP, in-memory). Good enough for small free-tier use.
_last_hits = {}
def rate_limit(key: str, max_per_minute=60):
    now = datetime.datetime.utcnow()
    window = now.replace(second=0, microsecond=0)
    k = f"{key}:{window.isoformat()}"
    _last_hits[k] = _last_hits.get(k, 0) + 1
    if _last_hits[k] > max_per_minute:
        abort(429, description="Too many requests — slow down.")

# ✅ Initialize DB immediately when app starts
with app.app_context():
    init_db()

# -------- Routes --------
@app.get("/")
def home():
    return render_template("index.html")

@app.get("/p/<code_id>")
def view_page(code_id):
    return render_template("view.html", code_id=code_id)

@app.post("/api/save")
def api_save():
    rate_limit(request.remote_addr or "anon")
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    title = (data.get("title") or "").strip()[:120]
    pin = (data.get("pin") or "").strip()

    if not content:
        return jsonify({"error": "content is required"}), 400

    code_id = generate_id()
    pin_hash = sha256(pin) if pin else None
    created_at = datetime.datetime.utcnow().isoformat()

    conn = _connect()
    c = conn.cursor()
    c.execute("INSERT INTO codes (id, title, content, pin_hash, created_at) VALUES (?, ?, ?, ?, ?)",
              (code_id, title, content, pin_hash, created_at))
    conn.commit()
    conn.close()

    return jsonify({
        "id": code_id,
        "url": (BASE_URL.rstrip("/") + "/p/" + code_id) if BASE_URL else ("/p/" + code_id)
    })

@app.post("/api/get")
def api_get():
    rate_limit(request.remote_addr or "anon")
    data = request.get_json(silent=True) or {}
    code_id = (data.get("id") or "").strip()
    pin = (data.get("pin") or "").strip()

    if not is_valid_id(code_id):
        return jsonify({"error": "invalid id"}), 400

    conn = _connect()
    c = conn.cursor()
    c.execute("SELECT id, title, content, pin_hash, created_at FROM codes WHERE id=?", (code_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "not found"}), 404

    if row["pin_hash"]:
        if not pin or sha256(pin) != row["pin_hash"]:
            return jsonify({"error": "pin required or incorrect"}), 403

    return jsonify({
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "created_at": row["created_at"]
    })

@app.get("/api/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

