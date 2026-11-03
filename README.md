# KarmaKiosk 🌙

Ein Onlineshop für digitale Downloads (Kartenlegungen • Zauber • Rituale) mit Login-Bereich, Benutzer- und Angebotsverwaltung – Fullstack in Python/Flask.

## Funktionen

- **Shop (öffentlich):** Angebote als Rechteck-Kacheln, Kategorien-Filter (Kartenlegungen, Zauber, Rituale), „Beliebte Artikel", Shop-Bewertung (4,9 ★ / 328 Bewertungen)
- **Login/Registrierung:** Session-basierte Authentifizierung, Passwörter gehasht (Werkzeug)
- **Admin-Bereich** (`/admin`, nur für Admins):
  - **Angebote verwalten:** hinzufügen, bearbeiten, entfernen, „beliebt" markieren, aktiv/inaktiv schalten
  - **Benutzer verwalten:** auflisten, Rollen (user/admin) ändern, Benutzer löschen

## Installation

```bash
pip install -r requirements.txt
python run.py
```

Der Shop läuft dann auf http://127.0.0.1:5000.

Beim ersten Start werden automatisch eine SQLite-Datenbank (`instance/karmakiosk.db`), ein Admin-Konto und Beispiel-Angebote angelegt.

**Standard-Admin-Zugangsdaten:**

- Benutzername: `admin`
- Passwort: `karmakiosk123`

> ⚠️ Passwort nach dem ersten Login ändern bzw. die Umgebungsvariablen `SECRET_KEY` und `DATABASE_URL` für den Produktiveinsatz setzen.

## Projektstruktur

```
run.py              # Einstiegspunkt
app.py              # App-Factory, DB, Login-Manager
models.py           # User- und Offer-Modelle (SQLAlchemy)
routes.py           # Auth-, Shop- und Admin-Routen
seed.py             # Startdaten (Admin + Beispiel-Angebote)
templates/          # Jinja2-Templates
static/css/         # Stylesheet (Holz-/Erdton-Design)
```
