import os
import math
from datetime import date, timedelta

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from dotenv import load_dotenv

from models import (
    db,
    User,
    Subject,
    Contribution,
    StudySession,
    Task,
    Goal,
    Friendship
)


load_dotenv()


app = Flask(__name__)


app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-secret-change-me"
)


database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///study_os.db"
)


# Render/Postgres URLs may use postgres://
# SQLAlchemy expects postgresql://

if database_url.startswith(
    "postgres://"
):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )


app.config[
    "SQLALCHEMY_DATABASE_URI"
] = database_url


app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False


db.init_app(app)


login_manager = LoginManager()

login_manager.login_view = "login"

login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# ============================================================
# DATABASE
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# HELPERS
# ============================================================

def seed_subjects(user):

    subjects = [
        ("Physics", "#7c9cff"),
        ("Chemistry", "#a78bfa"),
        ("Mathematics", "#4ade80"),
        ("Computer", "#38bdf8"),
        ("English", "#f59e0b"),
        ("Nepali", "#fb7185")
    ]

    for name, color in subjects:

        exists = Subject.query.filter_by(
            user_id=user.id,
            name=name
        ).first()

        if not exists:

            db.session.add(
                Subject(
                    user_id=user.id,
                    name=name,
                    color=color
                )
            )

    db.session.commit()


def current_streak(user_id):

    rows = Contribution.query.filter(
        Contribution.user_id == user_id,
        Contribution.pages > 0
    ).order_by(
        Contribution.day.desc()
    ).all()

    active = {
        row.day
        for row in rows
    }

    today = date.today()

    streak = 0

    current = today

    while current in active:

        streak += 1

        current -= timedelta(days=1)

    if streak == 0:

        current = today - timedelta(days=1)

        while current in active:

            streak += 1

            current -= timedelta(days=1)

    return streak


def best_streak(user_id):

    rows = Contribution.query.filter(
        Contribution.user_id == user_id,
        Contribution.pages > 0
    ).order_by(
        Contribution.day.asc()
    ).all()

    best = 0
    running = 0
    previous = None

    for row in rows:

        if (
            previous is not None
            and row.day == previous + timedelta(days=1)
        ):

            running += 1

        else:

            running = 1

        best = max(
            best,
            running
        )

        previous = row.day

    return best


def total_pages(user_id):

    result = db.session.query(
        db.func.sum(
            Contribution.pages
        )
    ).filter(
        Contribution.user_id == user_id
    ).scalar()

    return result or 0


def get_owned_subject_id(value, user_id):

    if value in (None, ""):

        return None

    try:

        subject_id = int(value)

    except (TypeError, ValueError):

        return None

    subject = Subject.query.filter_by(
        id=subject_id,
        user_id=user_id
    ).first()

    return subject.id if subject else None


# ============================================================
# AUTH
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )


    if request.method == "POST":

        username = (
            request.form["username"]
            .strip()
            .lower()
        )

        email = (
            request.form["email"]
            .strip()
            .lower()
        )

        password = request.form["password"]

        display_name = (
            request.form["display_name"]
            .strip()
        )


        if len(username) < 3:

            flash(
                "Username must be at least 3 characters."
            )

            return redirect(
                url_for("register")
            )


        if len(password) < 6:

            flash(
                "Password must be at least 6 characters."
            )

            return redirect(
                url_for("register")
            )


        if User.query.filter_by(
            username=username
        ).first():

            flash(
                "That username is already taken."
            )

            return redirect(
                url_for("register")
            )


        if User.query.filter_by(
            email=email
        ).first():

            flash(
                "That email is already registered."
            )

            return redirect(
                url_for("register")
            )


        user = User(

            username=username,

            email=email,

            display_name=(
                display_name
                or username
            ),

            password_hash=
                generate_password_hash(
                    password
                )

        )


        db.session.add(user)

        db.session.commit()


        seed_subjects(user)


        login_user(user)


        return redirect(
            url_for("dashboard")
        )


    return render_template(
        "register.html"
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )


    if request.method == "POST":

        username = (
            request.form["username"]
            .strip()
            .lower()
        )

        password = request.form["password"]


        user = User.query.filter_by(
            username=username
        ).first()


        if (
            user
            and check_password_hash(
                user.password_hash,
                password
            )
        ):

            login_user(user)

            return redirect(
                url_for("dashboard")
            )


        flash(
            "Invalid username or password."
        )


    return render_template(
        "login.html"
    )


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
@login_required
def dashboard():

    today = date.today()

    today_entry = Contribution.query.filter_by(
        user_id=current_user.id,
        day=today
    ).first()


    today_pages = (
        today_entry.pages
        if today_entry
        else 0
    )


    weekly_start = (
        today
        - timedelta(
            days=today.weekday()
        )
    )


    weekly_pages = db.session.query(
        db.func.sum(
            Contribution.pages
        )
    ).filter(
        Contribution.user_id ==
            current_user.id,
        Contribution.day >=
            weekly_start
    ).scalar() or 0


    study_minutes = db.session.query(
        db.func.sum(
            StudySession.minutes
        )
    ).filter(
        StudySession.user_id ==
            current_user.id
    ).scalar() or 0


    return render_template(
        "dashboard.html",

        today_pages=today_pages,

        weekly_pages=weekly_pages,

        study_minutes=study_minutes,

        total=total_pages(
            current_user.id
        ),

        current_streak=
            current_streak(
                current_user.id
            ),

        best_streak=
            best_streak(
                current_user.id
            )
    )


# ============================================================
# WRITING
# ============================================================

@app.route("/writing")
@login_required
def writing():

    subjects = Subject.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Subject.name
    ).all()


    return render_template(
        "writing.html",
        subjects=subjects
    )


@app.route(
    "/api/contributions"
)
@login_required
def contributions_api():

    rows = Contribution.query.filter_by(
        user_id=current_user.id
    ).all()


    return jsonify([

        {
            "day":
                row.day.isoformat(),

            "pages":
                row.pages,

            "subject_id":
                row.subject_id,

            "notes":
                row.notes

        }

        for row in rows

    ])


@app.route(
    "/api/contributions",
    methods=["POST"]
)
@login_required
def save_contribution():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "A JSON object is required."
        }), 400


    try:

        selected_day = date.fromisoformat(
            data["day"]
        )

        pages = float(
            data.get(
                "pages",
                0
            )
        )

    except (KeyError, TypeError, ValueError):

        return jsonify({
            "error": "Invalid data."
        }), 400


    if pages < 0 or not math.isfinite(pages):

        return jsonify({
            "error":
                "Pages cannot be negative."
        }), 400

    subject_id = get_owned_subject_id(
        data.get("subject_id"),
        current_user.id
    )

    if data.get("subject_id") not in (None, "") and subject_id is None:

        return jsonify({
            "error": "Invalid subject."
        }), 400


    entry = Contribution.query.filter_by(
        user_id=current_user.id,
        day=selected_day
    ).first()


    if pages == 0 and not data.get(
        "notes",
        ""
    ):

        if entry:

            db.session.delete(entry)

    else:

        if not entry:

            entry = Contribution(

                user_id=current_user.id,

                day=selected_day

            )

            db.session.add(entry)


        entry.pages = pages

        entry.notes = data.get(
            "notes",
            ""
        )

        entry.subject_id = subject_id


    db.session.commit()


    return jsonify({
        "ok": True
    })


# ============================================================
# LEADERBOARD
# ============================================================

@app.route("/leaderboard")
@login_required
def leaderboard():

    users = User.query.all()


    ranking = []


    for user in users:

        pages = total_pages(
            user.id
        )

        ranking.append({

            "username":
                user.username,

            "display_name":
                user.display_name,

            "pages":
                pages,

            "streak":
                current_streak(
                    user.id
                )

        })


    ranking.sort(
        key=lambda x: x["pages"],
        reverse=True
    )


    return render_template(
        "leaderboard.html",
        ranking=ranking
    )


# ============================================================
# FRIENDS
# ============================================================

@app.route("/friends")
@login_required
def friends():

    friendships = Friendship.query.filter(
        (
            (Friendship.requester_id ==
             current_user.id)
            |
            (Friendship.addressee_id ==
             current_user.id)
        ),
        Friendship.status == "accepted"
    ).all()


    friend_ids = []

    for friendship in friendships:

        if friendship.requester_id == \
                current_user.id:

            friend_ids.append(
                friendship.addressee_id
            )

        else:

            friend_ids.append(
                friendship.requester_id
            )


    friends_list = User.query.filter(
        User.id.in_(friend_ids)
    ).all()


    return jsonify([

        {
            "username":
                friend.username,

            "display_name":
                friend.display_name

        }

        for friend in friends_list

    ])


# ============================================================
# STUDY SESSION
# ============================================================

@app.route(
    "/api/study-session",
    methods=["POST"]
)
@login_required
def save_study_session():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "A JSON object is required."
        }), 400

    try:

        session_day = date.fromisoformat(data["day"])
        minutes = int(data["minutes"])

    except (KeyError, TypeError, ValueError):

        return jsonify({
            "error": "Invalid study session data."
        }), 400

    if minutes <= 0:

        return jsonify({
            "error": "Minutes must be greater than zero."
        }), 400

    subject_id = get_owned_subject_id(
        data.get("subject_id"),
        current_user.id
    )

    if data.get("subject_id") not in (None, "") and subject_id is None:

        return jsonify({
            "error": "Invalid subject."
        }), 400


    session = StudySession(

        user_id=current_user.id,

        day=session_day,

        minutes=minutes,

        subject_id=subject_id,

        notes=data.get(
            "notes",
            ""
        )

    )


    db.session.add(session)

    db.session.commit()


    return jsonify({
        "ok": True
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=os.getenv("FLASK_DEBUG", "0") == "1"
    )