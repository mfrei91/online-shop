# 🏠 Homeserver-Setup: Abgetrennter Bereich mit eigener externer Festplatte

> Ziel: Der Shop läuft in einem isolierten Bereich deines Homeservers.
> Alle Daten (SQLite-Datenbank, Dateien) liegen auf einer **eigenen externen
> Festplatte**, und der Dienst läuft als **eigener Benutzer** mit minimalen
> Rechten. Anleitung für Linux (Debian/Ubuntu, z. B. Raspberry Pi OS).

---

## 1. Externe Festplatte vorbereiten und dauerhaft einbinden

> ⚠️ Formatieren löscht alle Daten auf der Platte – vorher prüfen, ob sie leer ist!

### 1.1 Platte identifizieren

```bash
lsblk -f
# z. B.: sda mit ext4 oder leer. Platte merken (hier: /dev/sda)
```

### 1.2 Platte mit ext4 formatieren (nur wenn neu/leer)

```bash
sudo mkfs.ext4 -L karmakiosk /dev/sda
```

### 1.3 Dauerhaften Mountpunkt anlegen

```bash
sudo mkdir -p /srv/karmakiosk
```

### 1.4 UUID herausfinden

```bash
sudo blkid /dev/sda
# Ausgabe: UUID="xxxx-xxxx-..." TYPE="ext4"
```

### 1.5 In `/etc/fstab` eintragen (übersteht Neustarts)

```bash
sudo nano /etc/fstab
# Diese Zeile ergänzen (UUID einsetzen):
UUID=xxxx-xxxx-xxxx  /srv/karmakiosk  ext4  defaults,nofail  0  2
```

```bash
sudo systemctl daemon-reload
sudo mount -a
df -h /srv/karmakiosk   # Platte sollte jetzt hier erscheinen
```

`nofail` sorgt dafür, dass der Server auch startet, wenn die Platte mal abgezogen ist.

---

## 2. Eigenen Benutzer für den Shop anlegen (Isolation)

```bash
sudo useradd --system --home /srv/karmakiosk/app --shell /usr/sbin/nologin karmakiosk
sudo mkdir -p /srv/karmakiosk/app /srv/karmakiosk/data
```

- `--system` + `nologin`: Der Benutzer kann sich nicht interaktiv anmelden
- `/srv/karmakiosk/app` → Programmcode
- `/srv/karmakiosk/data` → Datenbank & Dateien (später alles Wichtige)

Rechte vergeben (nur der neue Benutzer darf schreiben):

```bash
sudo chown -R karmakiosk:karmakiosk /srv/karmakiosk
sudo chmod 750 /srv/karmakiosk/app /srv/karmakiosk/data
```

---

## 3. Shop in den abgetrennten Bereich installieren

```bash
sudo apt install python3 python3-venv git

# Code als Benutzer karmakiosk in den Bereich legen
sudo -u karmakiosk git clone https://github.com/mfrei91/online-shop.git /srv/karmakiosk/app

# Virtuelle Umgebung einrichten
sudo -u karmakiosk /usr/bin/python3 -m venv /srv/karmakiosk/app/.venv
sudo -u karmakiosk /srv/karmakiosk/app/.venv/bin/pip install -r /srv/karmakiosk/app/requirements.txt
sudo -u karmakiosk /srv/karmakiosk/app/.venv/bin/pip install gunicorn
```

Datenbank auf die externe Platte legen – die App unterstützt das über die
Umgebungsvariable `DATABASE_URL` (SQLite-Pfad frei wählbar):

```
DATABASE_URL=sqlite:////srv/karmakiosk/data/karmakiosk.db
SECRET_KEY=<langer Zufallswert, z. B. aus: openssl rand -hex 32>
```

> Das Secret niemals in Dateien im Repo speichern – nur in der
> systemd-Unit (Schritt 4) oder einer geschützten Datei unter `/srv/karmakiosk`.

Kurzer Testlauf:

```bash
sudo -u karmakiosk DATABASE_URL=sqlite:////srv/karmakiosk/data/karmakiosk.db \
  SECRET_KEY=test /srv/karmakiosk/app/.venv/bin/python /srv/karmakiosk/app/run.py
# http://homeserver-ip:5000 prüfen, dann mit Strg+C beenden
```

---

## 4. Als isolierter systemd-Dienst einrichten (Autostart + Sandbox)

```bash
sudo nano /etc/systemd/system/karmakiosk.service
```

Inhalt:

```ini
[Unit]
Description=KarmaKiosk Onlineshop
After=network.target

[Service]
User=karmakiosk
Group=karmakiosk
WorkingDirectory=/srv/karmakiosk/app
Environment=DATABASE_URL=sqlite:////srv/karmakiosk/data/karmakiosk.db
Environment=SECRET_KEY=<dein-geheimer-schluessel>
ExecStart=/srv/karmakiosk/app/.venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 run:app
Restart=on-failure

# --- Isolation / Sandbox ---
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/karmakiosk/data
# Wenn der Shop nichts am System ändern soll, ist das der wichtigste Teil:
# Schreibzugriffe NUR auf /srv/karmakiosk/data (die externe Platte) erlaubt.

[Install]
WantedBy=multi-user.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now karmakiosk
systemctl status karmakiosk
```

Jetzt läuft der Shop dauerhaft (auch nach Neustart), nur als Benutzer
`karmakiosk`, nur mit Schreibrechten auf dem Datenordner der externen Platte.

---

## 5. Nach außen freigeben (HTTPS über Reverse-Proxy)

Gunicorn lauscht bewusst nur auf `127.0.0.1:8000` (nur lokal erreichbar).
Nach außen geht es über einen Reverse-Proxy mit HTTPS:

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

```bash
sudo nano /etc/nginx/sites-available/karmakiosk
```

```nginx
server {
    server_name karmakiosk.deine-domain.example;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/karmakiosk /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d karmakiosk.deine-domain.example   # kostenloses HTTPS-Zertifikat
```

Voraussetzungen: DynDNS/Feste IP + Portfreigabe 80/443 im Router – oder ohne
Portfreigabe per Cloudflare Tunnel / nur für dich per Tailscale.

---

## 6. Backup der externen Platte

Alles Wichtige liegt in **einer** Datei auf einer Platte – daher regelmäßig
woanders hin sichern (der Sinn einer *eigenen* Platte ist Isolation, kein Backup!):

```bash
# Beispieleintrag per Cron (jede Nacht 3 Uhr nach /home/backup auf dem Server):
0 3 * * * cp /srv/karmakiosk/data/karmakiosk.db /home/backup/karmakiosk-$(date +\%F).db
```

---

## Übersicht

```
/srv/karmakiosk/          ← externe Festplatte (ext4, fstab-Mount)
├── app/                  ← Shop-Code (Benutzer: karmakiosk)
└── data/                 ← SQLite-Datenbank + Dateien (der einzige Schreibbereich)
                          ← wird per DATABASE_URL dort hin verlegt

Benutzer: karmakiosk (Systembenutzer, keine Anmeldung)
Dienst:  systemd (Autostart, Restart, Sandbox: ReadWritePaths nur data/)
Netz:    gunicorn nur lokal → nginx + Let's Encrypt HTTPS
```
