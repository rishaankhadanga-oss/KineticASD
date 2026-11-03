# KineticASD — Python/FastAPI HOSA Prototype

Browser-based educational prototype with parent/caregiver and therapist portal previews, SQLite-backed synthetic ABC observations, shared timeline, filters, descriptive charts, audit-event demo, and simulated therapist-verification applications.

## Safety and scope
- **Synthetic demo data only. Do not enter real patient information or PHI.**
- This prototype is not HIPAA compliant, has not undergone a security review, and is not for clinical use.
- The role selector is only a UI preview. There is no real login or authorization; API routes are not protected.
- Therapist application decisions are simulated and do not verify identities, licenses, or credentials.
- Charts show descriptive record counts, not diagnoses, causes, or evidence of clinical improvement.

## Run on Windows
1. Extract the ZIP and open the folder in VS Code.
2. In the terminal, create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell activation is blocked, use Command Prompt: `.venv\Scripts\activate.bat`
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Start the server: `python -m uvicorn main:app --reload`
5. Open the site at http://127.0.0.1:8000 and API docs at http://127.0.0.1:8000/docs.

## macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## Database and reset
`kineticasd_demo.db` is created beside `main.py` and stores synthetic records between restarts. Stop the server and delete this file to reset the demo; it will be seeded again at next startup.

## Endpoints
- `GET /api/health`
- `GET /api/observations` (optional `setting`, `discipline`, `search` filters)
- `POST /api/observations`
- `GET /api/summary`
- `GET /api/audit`
- `GET /api/demo-permissions`
- `GET /api/therapist-applications`
- `POST /api/therapist-applications/{application_id}/decision?decision=approve|reject`

## Tests
Run `python -m unittest discover -s tests -v`. Tests check basic API/database behavior; they do not certify security or HIPAA compliance.

## Deploy a shareable demo website (Railway)

This section is for a public **synthetic-data demonstration only**. The app has no real authentication or authorization: anyone with the public URL can view the demo records and use the demo write actions. Never enter real patient information, PHI, passwords, or private records.

### 1. Put the project in GitHub
1. Extract this ZIP.
2. Sign in to GitHub and create a **private** repository named `KineticASD` (a private repository protects the source code, not the deployed public website).
3. Upload the files and folders *inside* `KineticASD_Python_Prototype` to the repository root. Make sure `main.py`, `requirements.txt`, and `railway.toml` are at the top level, and `static/index.html` is present.
4. Do not upload `.venv`, `.env`, or any database file. `.gitignore` excludes these common local files.

### 2. Deploy the app
1. With a parent/guardian's help, create or sign in to a Railway account and review current pricing, trial limits, and account requirements before confirming anything that could cost money.
2. In Railway, create a project and choose **Deploy from GitHub repo**; select the `KineticASD` repository.
3. Railway should detect Python and use `railway.toml`. The start command binds Uvicorn to the port provided by the host.
4. In the service's **Variables** settings, add:
   - `KINETICASD_DB=/data/kineticasd_demo.db`
5. In the project/service canvas, create a **Volume** attached to this service and set its mount path to:
   - `/data`
6. Generate a public domain in the service's networking/settings. Wait for deployment to finish.
7. Open the generated HTTPS URL in Chrome. Check that the home page loads and that `<your-domain>/api/health` returns JSON with `"status":"ok"`.

### 3. Confirm persistence
1. Add a clearly fictional observation in the demo.
2. Refresh the page and confirm it remains.
3. Restart/redeploy the service and confirm it remains. Do not delete the volume: it contains the demo database.

### Important hosting notes
- A persistent volume is required for SQLite data to survive restarts/redeploys. Without the `/data` volume and `KINETICASD_DB` variable, local database changes may be lost when the host replaces the container.
- Hosting plans, free allowances, domain availability, and prices can change. Review the provider's current terms with a parent/guardian before deploying or enabling billing.
- The deployed app is a public, unauthenticated HOSA demo. The parent/therapist role selector is only a visual simulation; it does not restrict API access. Anyone with the link can read, add, and change synthetic demo content. Do not use this deployment for real people, clinical decisions, or confidential information.
- This prototype is not HIPAA compliant, has not received a security review, and is not suitable for clinical use.
