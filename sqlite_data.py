import os
from abc import ABC

from flask_sqlalchemy import SQLAlchemy
from config import BaseModel
from models import User, Sport, SportInterest, Playdate, Participant
import requests


class SQLiteSportBuddyDataManager(BaseModel, ABC):
    def __init__(self, db: SQLAlchemy):
        """Initialize the SQLiteSportBuddyDataManager with the SQLAlchemy instance."""
        self.db = db

    def get_all_users(self):
        """Return a list of all users."""
        return User.query.all()

    def get_all_sports(self):
        """Return a list of all sports."""
        return Sport.query.all()

    def get_all_sport_interest(self):
        """Return sport interest."""
        return SportInterest.query.all()

    def get_user_playdates_created(self, user_id):
        """Return a list of events for a specific user."""
        user = User.query.get(user_id)
        return user.playdates_created if user else []

    def add_user(self, user):
        """Add a new user to the database."""
        self.db.session.add(user)
        self.db.session.commit()

    def remove_user(self, user_id):
        """Remove a user from the database."""
        user = User.query.get(user_id)
        if user:
            self.db.session.delete(user)
            self.db.session.commit()

    def add_sport(self, sport):
        """Add a new sport to the database."""
        self.db.session.add(sport)
        self.db.session.commit()

    def add_playdate(self, playdate):
        """Add a new event (playdate) to the database."""
        self.db.session.add(playdate)
        self.db.session.commit()

    def update_playdate(self, playdate_id, updated_playdate_data):
        """Update the details of a specific event in the database."""
        playdate = Playdate.query.get(playdate_id)
        if playdate:
            for key, value in updated_playdate_data.items():
                if hasattr(playdate, key):
                    setattr(playdate, key, value)
            self.db.session.commit()

    def delete_playdate(self, playdate_id):
        """Delete a specific playdate from the database."""
        playdate = Playdate.query.get(playdate_id)
        if playdate:
            self.db.session.delete(playdate)
            self.db.session.commit()

    def get_playdate_by_id(self, playdate_id):
        """Get a playdate by its ID."""
        return Playdate.query.get(playdate_id)

    def get_user_by_id(self, user_id):
        """Get a user by their ID."""
        return User.query.get(user_id)

    def get_sport_by_id(self, sport_id):
        """Get a sport by its ID."""
        return Sport.query.get(sport_id)

    def get_user_by_username(self, username):
        """Return a user by their username."""
        return User.query.filter_by(username=username).first()

    def get_users_nearby(self, latitude, longitude, radius=10):
        """Fetch users nearby based on latitude/longitude."""
        # This method assumes your User model has `latitude` and `longitude` fields.
        # It filters users within a certain radius from the given coordinates.
        # Implement your own logic or use a geospatial library (like GeoAlchemy) for better geospatial queries.
        nearby_users = User.query.filter(
            (User.latitude - latitude) ** 2 + (User.longitude - longitude) ** 2 <= radius ** 2
        ).all()
        return nearby_users

    def add_sport_interest(self, user_id, sport_id):
        """Add a new sport interest for a user."""
        sport_interest = SportInterest(user_id=user_id, sport_id=sport_id)
        self.db.session.add(sport_interest)
        self.db.session.commit()

    def fetch_event_details(self, event_name):
        """Fetch event details from an external API (if applicable)."""
        # Placeholder for external API integration
        api_url = f"https://api.example.com/events/{event_name}"
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        return None

    def add_participant(self, user_id, playdate_id):
        """Add a user as a participant to a playdate."""
        playdate = Playdate.query.get(playdate_id)
        if playdate:
            if playdate.max_participants and len(playdate.participants) >= playdate.participants:
                raise ValueError("This playdate has reached the maximum number of participants.")
        participant = Participant(user_id=user_id, playdate_id=playdate_id)
        self.db.session.add(participant)
        self.db.session.commit()

    def remove_participant(self, user_id, playdate_id):
        """Remove a user from a playdate's participants."""
        participant = Participant.query.filter_by(user_id=user_id, playdate_id=playdate_id).first()
        if participant:
            self.db.session.delete(participant)
            self.db.session.commit()

    def get_playdate_participants(self, playdate_id):
        """Get a list of participants for a specific playdate."""
        playdate = Playdate.query.get(playdate_id)
        return [participant.user for participant in playdate.participants] if playdate else []
