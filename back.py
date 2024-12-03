from abc import ABC, abstractmethod


class BaseModel(ABC):

    @abstractmethod
    def get_all_users(self):
        """Return a list of all users."""
        pass

    @abstractmethod
    def get_user_events(self, user_id):
        """Return a list of events (playdates) for a specific user."""
        pass

    @abstractmethod
    def add_user(self, user):
        """Add a new user to the data source."""
        pass

    @abstractmethod
    def remove_user(self, user_id):
        """Remove a user from the data source."""
        pass

    @abstractmethod
    def add_event(self, user_id, event):
        """Add a new event (playdate) to the data source."""
        pass

    @abstractmethod
    def update_event(self, user_id, event):
        """Update the details of a specific event (playdate) in the data source."""
        pass

    @abstractmethod
    def delete_event(self, user_id, event_id):
        """Delete an event (playdate) from the data source."""
        pass

    @abstractmethod
    def get_event_by_id(self, event_id):
        """Get an event by its ID."""
        pass

    @abstractmethod
    def get_user_by_id(self, user_id):
        """Get a user by their ID."""
        pass

    @abstractmethod
    def get_user_by_username(self, username):
        """Return a user by their username."""
        pass

    @abstractmethod
    def get_users_nearby(self, latitude, longitude, radius=10):
        """Fetch users nearby based on latitude/longitude."""
        pass

    @abstractmethod
    def fetch_event_details(self, event_name):
        """Fetch event details from an external API or data source."""
        pass