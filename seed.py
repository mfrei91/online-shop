from app import db
from models import Offer, User

DEFAULT_OFFERS = [
    ("Liebes-Tarot", "Drei-Karten-Legung zu Liebe & Partnerschaft als PDF-Download.", 9.99, "Kartenlegungen", "🃏", True),
    ("Jahreslegung", "12 Karten für deine 12 Monate – ausführliche Deutung.", 19.99, "Kartenlegungen", "🎴", True),
    ("Keltenkreuz", "Die klassische Großlegung für tiefe Fragen.", 14.99, "Kartenlegungen", "🌙", False),
    ("Glückszauber", "Anleitung & Zutatenliste für dein eigenes Glücksamulett.", 7.99, "Zauber", "✨", True),
    ("Schutzritual", "Kraftvolles Schutzritual für Zuhause, mit Anleitung.", 12.99, "Rituale", "🕯️", True),
    ("Vollmond-Ritual", "Manifestationsritual zum nächsten Vollmond.", 11.99, "Rituale", "🌕", False),
    ("Reinigungszauber", "Aura-Reinigung mit Salbei & Klangschale – Schritt-für-Schritt.", 8.99, "Zauber", "🧿", False),
]


def seed(app):
    if not User.query.filter_by(role="admin").first():
        admin = User(
            username="admin",
            email="admin@karmakiosk.shop",
            role="admin",
        )
        admin.set_password("karmakiosk123")
        db.session.add(admin)
        db.session.commit()

    if Offer.query.count() == 0:
        for title, description, price, category, emoji, popular in DEFAULT_OFFERS:
            db.session.add(
                Offer(
                    title=title,
                    description=description,
                    price=price,
                    category=category,
                    emoji=emoji,
                    popular=popular,
                )
            )
        db.session.commit()
        app.logger.info("Beispiel-Angebote wurden erstellt.")
