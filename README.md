# Batch Code Share (Free)
Paste code, get a short ID, share with friends. Optional PIN. Built with Flask + SQLite. Ready for free hosting on Render.

## Features
- Paste any text/code (400+ lines OK)
- 7-char ID (e.g., `A9f3zQ7`)
- Optional PIN for privacy (stored as SHA-256 hash)
- Simple UI (dark theme)
- Free-tier deploy on Render, static assets bundled
- API routes: `/api/save`, `/api/get`

## Local Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

## Deploy on Render (₹0)
1. Create a public GitHub repo and push these files.
2. Go to Render.com → New → Web Service → Connect your repo.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app`
5. Plan: **Free**. Click Create.
6. After deploy, open the URL and test. Optionally set environment variable `BASE_URL` to your Render domain.
7. Storage: The `codes.db` file lives on the instance disk. On free tier, dynos can spin down; consider exporting if you need backups.

## Usage
- Create: Paste content on `/` and click **Save & Get ID**. Share the ID or link shown.
- Retrieve: Enter ID (and PIN if set) to get the content. Or directly open `/p/<id>`.

## Security Notes
- Do **not** store passwords or private keys.
- PIN is optional & hashed (SHA-256). It prevents casual access but is not bulletproof.
- Free-tier apps sleep; first request may be slow to wake.

## License
MIT
