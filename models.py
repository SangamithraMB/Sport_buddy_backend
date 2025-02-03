from enum import Enum
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    sport_interests = db.relationship('SportInterest', backref='user', lazy=True)
    playdates = db.relationship('Playdate', backref='creator', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def __str__(self):
        return self.username


class SportType(Enum):
    SINGLE = "Single"
    TEAM = "Team"
    BOTH = "Both"


class Sport(db.Model):
    __tablename__ = 'sports'

    id = db.Column(db.Integer, primary_key=True)
    sport_name = db.Column(db.String(100), nullable=False, index=True)
    sport_type = db.Column(db.Enum(SportType), nullable=False, default=SportType.BOTH)

    def __repr__(self):
        return f'<Sport {self.sport_name}>'

    def __str__(self):
        return f"{self.sport_name} ({self.sport_type.value})"


class SportInterest(db.Model):
    __tablename__ = 'sport_interests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sport_id = db.Column(db.Integer, db.ForeignKey('sports.id'), nullable=False)

    def __repr__(self):
        return f'<SportInterest User {self.user_id} interested in Sport {self.sport_id}>'

    def __str__(self):
        return f"Interest in {self.sport_id}"


class Playdate(db.Model):
    __tablename__ = 'playdates'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    sport_id = db.Column(db.Integer, db.ForeignKey('sports.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    max_participants = db.Column(db.Integer, nullable=True, default=None)

    participants = db.relationship('Participant', backref='playdate', lazy=True)

    def __repr__(self):
        return f'<Playdate {self.title} for Sport {self.sport_id} at {self.address}>'

    def __str__(self):
        return f"{self.title} ({self.date})"


class Participant(db.Model):
    __tablename__ = 'participants'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdates.id'), nullable=False)

    def __repr__(self):
        return f'<Participant User {self.user_id} in Playdate {self.playdate_id}>'


class MessageType(Enum):
    TEXT = "Text"
    AUDIO = "Audio"
    VIDEO = "Video"
    IMAGE = "Image"


class Chat(db.Model):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String, nullable=False)
    message_type = db.Column(db.Enum(MessageType), nullable=False, default=MessageType.TEXT)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='sent')

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

    def __repr__(self):
        return f"<Chat(sender_id={self.sender_id}, receiver_id={self.receiver_id}, message={self.message})>"
