from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from app import db
from constants import CATEGORIES
from models import Offer, User

auth = Blueprint("auth", __name__)
shop = Blueprint("shop", __name__)
admin = Blueprint("admin", __name__, url_prefix="/admin")


def register_blueprints(app):
    app.register_blueprint(auth)
    app.register_blueprint(shop)
    app.register_blueprint(admin)


def admin_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)

    return wrapper


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("shop.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not email or len(password) < 6:
            flash("Bitte alle Felder ausfüllen (Passwort min. 6 Zeichen).", "error")
        elif User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            flash("Benutzername oder E-Mail ist bereits vergeben.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Willkommen bei KarmaKiosk! 🌙", "success")
            return redirect(url_for("shop.index"))
    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("shop.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Erfolgreich angemeldet.", "success")
            return redirect(request.args.get("next") or url_for("shop.index"))
        flash("Benutzername oder Passwort ist falsch.", "error")
    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Du wurdest abgemeldet.", "success")
    return redirect(url_for("shop.index"))


@shop.route("/")
def index():
    category = request.args.get("kategorie")
    query = Offer.query.filter_by(active=True)
    if category in CATEGORIES:
        query = query.filter_by(category=category)
    offers = query.order_by(Offer.id.desc()).all()
    return render_template(
        "index.html",
        offers=offers,
        categories=CATEGORIES,
        active_category=category,
        popular=Offer.query.filter_by(active=True, popular=True).all(),
    )


@admin.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "offers": Offer.query.count(),
        "active": Offer.query.filter_by(active=True).count(),
        "admins": User.query.filter_by(role="admin").count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin.route("/angebote")
@login_required
@admin_required
def offers():
    offers = Offer.query.order_by(Offer.id.desc()).all()
    return render_template("admin/offers.html", offers=offers, categories=CATEGORIES)


@admin.route("/angebote/neu", methods=["GET", "POST"])
@login_required
@admin_required
def offer_create():
    if request.method == "POST":
        offer = Offer(
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip(),
            price=_parse_price(request.form.get("price", "0")),
            category=request.form.get("category", CATEGORIES[0]),
            emoji=request.form.get("emoji", "🔮").strip() or "🔮",
            popular=bool(request.form.get("popular")),
            active=True,
            author_id=current_user.id,
        )
        if not offer.title:
            flash("Bitte einen Titel angeben.", "error")
            return render_template("admin/offer_form.html", offer=offer, categories=CATEGORIES)
        db.session.add(offer)
        db.session.commit()
        flash(f"Angebot „{offer.title}“ wurde hinzugefügt.", "success")
        return redirect(url_for("admin.offers"))
    return render_template("admin/offer_form.html", offer=None, categories=CATEGORIES)


@admin.route("/angebote/<int:offer_id>/bearbeiten", methods=["GET", "POST"])
@login_required
@admin_required
def offer_edit(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    if request.method == "POST":
        if request.form.get("delete"):
            db.session.delete(offer)
            db.session.commit()
            flash(f"Angebot „{offer.title}“ wurde entfernt.", "success")
            return redirect(url_for("admin.offers"))
        offer.title = request.form.get("title", "").strip() or offer.title
        offer.description = request.form.get("description", "").strip()
        offer.price = _parse_price(request.form.get("price", "0"))
        offer.category = request.form.get("category", offer.category)
        offer.emoji = request.form.get("emoji", "🔮").strip() or "🔮"
        offer.popular = bool(request.form.get("popular"))
        offer.active = bool(request.form.get("active"))
        db.session.commit()
        flash(f"Angebot „{offer.title}“ wurde gespeichert.", "success")
        return redirect(url_for("admin.offers"))
    return render_template("admin/offer_form.html", offer=offer, categories=CATEGORIES)


@admin.route("/angebote/<int:offer_id>/loeschen", methods=["POST"])
@login_required
@admin_required
def offer_delete(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash(f"Angebot „{offer.title}“ wurde entfernt.", "success")
    return redirect(url_for("admin.offers"))


@admin.route("/benutzer")
@login_required
@admin_required
def users():
    users = User.query.order_by(User.id).all()
    return render_template("admin/users.html", users=users)


@admin.route("/benutzer/<int:user_id>/rolle", methods=["POST"])
@login_required
@admin_required
def user_role(user_id):
    user = User.query.get_or_404(user_id)
    role = request.form.get("role")
    if role in ("user", "admin"):
        if user.id == current_user.id and role == "user":
            flash("Du kannst dir nicht selbst die Admin-Rolle entziehen.", "error")
        else:
            user.role = role
            db.session.commit()
            flash(f"Rolle von „{user.username}“ wurde geändert.", "success")
    return redirect(url_for("admin.users"))


@admin.route("/benutzer/<int:user_id>/loeschen", methods=["POST"])
@login_required
@admin_required
def user_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Du kannst dein eigenes Konto nicht löschen.", "error")
    else:
        Offer.query.filter_by(author_id=user.id).update({"author_id": None})
        db.session.delete(user)
        db.session.commit()
        flash(f"Benutzer „{user.username}“ wurde gelöscht.", "success")
    return redirect(url_for("admin.users"))


def _parse_price(value):
    try:
        return round(float(str(value).replace(",", ".").replace("€", "").strip()), 2)
    except (ValueError, TypeError):
        return 0.0
