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
        self.mapbox_api_key = os.getenv("mapbox_api_key")

    def get_all_users(self):
        """Return a list of all users."""
        return User.query.all()

    def get_all_sports(self):
        """Return a list of all sports."""
        return Sport.query.all()

    def get_all_sport_interest(self, user_id, sport_id):
        """Return sport interest based on user_id and sport_id."""
        sport_interest = SportInterest.query.get(user_id, sport_id)
        return sport_interest.sport_interest_added if sport_interest else []

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

    def add_sport_interest(self, user_id, sport_id):
        """Add a new sport interest for a user."""
        sport_interest = SportInterest(user_id=user_id, sport_id=sport_id)
        self.db.session.add(sport_interest)
        self.db.session.commit()

    def add_participant(self, user_id, playdate_id):
        """Add a user as a participant to a playdate."""
        playdate = Playdate.query.get(playdate_id)
        if playdate:
            current_participants = len(playdate.participants)
            if playdate.max_participants and current_participants >= playdate.max_participants:
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

    def get_location_coordinates(self, address: str, limit: int = 1):
        """
        Fetch latitude and longitude from Mapbox for a given place name.

        :param address: The name of the place to geocode.
        :param limit: Number of results to retrieve (default is 1).
        :return: Tuple of (latitude, longitude) if successful, otherwise (None, None).
        """
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
        params = {
            'access_token': self.mapbox_api_key,
            'limit': limit
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get('features'):
                print(f"No geolocation data found for {address}.")
                return None, None

            latitude = data['features'][0]['geometry']['coordinates'][1]
            longitude = data['features'][0]['geometry']['coordinates'][0]
            return latitude, longitude

        except requests.RequestException as e:
            print(f"Error fetching location for {address}: {e}")
            return None, None
        except KeyError:
            print("Unexpected response structure from Mapbox.")
            return None, None
