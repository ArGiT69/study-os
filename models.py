from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    display_name = db.Column(
        db.String(80),
        nullable=False
    )

    daily_page_goal = db.Column(
        db.Float,
        default=8
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Subject(db.Model):

    __tablename__ = "subjects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    name = db.Column(
        db.String(80),
        nullable=False
    )

    color = db.Column(
        db.String(20),
        default="#8b9bb4"
    )


class Contribution(db.Model):

    __tablename__ = "contributions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    day = db.Column(
        db.Date,
        nullable=False
    )

    pages = db.Column(
        db.Float,
        default=0
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=True
    )

    notes = db.Column(
        db.Text,
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "day",
            name="unique_user_day"
        ),
    )


class StudySession(db.Model):

    __tablename__ = "study_sessions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=True
    )

    day = db.Column(
        db.Date,
        nullable=False
    )

    minutes = db.Column(
        db.Integer,
        nullable=False
    )

    notes = db.Column(
        db.Text,
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=True
    )

    due_date = db.Column(
        db.Date,
        nullable=True
    )

    priority = db.Column(
        db.String(20),
        default="normal",
        nullable=False
    )

    completed = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class Goal(db.Model):

    __tablename__ = "goals"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    goal_type = db.Column(
        db.String(50),
        nullable=False
    )

    target = db.Column(
        db.Float,
        nullable=False
    )

    current = db.Column(
        db.Float,
        default=0
    )

    deadline = db.Column(
        db.Date,
        nullable=True
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )


class Friendship(db.Model):

    __tablename__ = "friendships"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    requester_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    addressee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "requester_id",
            "addressee_id",
            name="unique_friend_request"
        ),
    )