import os
from datetime import datetime

from flask_migrate import Migrate
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from models import User, Playdate, db, Sport, SportInterest, SportType
from sqlite_data import SQLiteSportBuddyDataManager

load_dotenv()

app = Flask(__name__)
migrate = Migrate(app, db)
# Configuring SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "data", "sport_buddy.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

data_manager = SQLiteSportBuddyDataManager(db)


@app.route('/')
def home():
    return "Welcome to the Sport Buddy API!"


# Endpoint to create a new user
@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')

    new_user = User(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
    data_manager.add_user(new_user)

    return jsonify({"message": "User created successfully!"}), 201


@app.route('/sports', methods=['POST'])
def add_sport():
    data = request.get_json()

    # Validate that the required fields are present
    if not data.get('sport_name'):
        return jsonify({'error': 'Sport name is required'}), 400
    if 'sport_type' in data and data['sport_type'] not in [e.value for e in SportType]:
        return jsonify({'error': 'Invalid sport type'}), 400

    try:
        # Set the sport_type to SportType.BOTH by default, or use the one provided in the request
        sport_type = SportType[data['sport_type'].upper()] if 'sport_type' in data else SportType.BOTH

        # Create a new sport instance
        new_sport = Sport(
            sport_name=data['sport_name'],
            sport_type=sport_type
        )

        # Add to the session and commit to the database
        db.session.add(new_sport)
        db.session.commit()

        # Return the created sport data
        return jsonify({
            'id': new_sport.id,
            'sport_name': new_sport.sport_name,
            'sport_type': new_sport.sport_type.value
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Endpoint to get all users
@app.route('/users', methods=['GET'])
def get_users():
    users = data_manager.get_all_users()
    users_data = [{"id": user.id, "username": user.username} for user in users]
    return jsonify(users_data)


@app.route('/sports', methods=['GET'])
def get_sports():
    sports = data_manager.get_all_sports()
    sports_data = [{"id": sport.id, "sport_name": sport.sport_name, 'sport_type': sport.sport_type.value}
                   for sport in sports]
    return jsonify(sports_data)


# Endpoint to get a user's details by ID
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = data_manager.get_user_by_id(user_id)
    if user:
        user_data = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
        return jsonify(user_data)
    return jsonify({"message": "User not found!"}), 404


# Endpoint to create a playdate (event)
@app.route('/playdates', methods=['POST'])
def add_playdate():
    data = request.get_json()

    # Ensure all required fields are present
    if not all(k in data for k in ('title', 'sport_id', 'creator_id', 'address', 'longitude', 'latitude', 'date')):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Parse the 'date' string to a Python datetime object
        playdate_date = datetime.strptime(data['date'], '%d-%m-%Y %H:%M:%S')

        # Create a new playdate
        new_playdate = Playdate(
            title=data['title'],
            sport_id=data['sport_id'],
            creator_id=data['creator_id'],
            address=data['address'],
            longitude=data['longitude'],
            latitude=data['latitude'],
            date=playdate_date,
            max_participants=data.get('max_participants')
        )

        # Add to the session and commit to the database
        db.session.add(new_playdate)
        db.session.commit()

        return jsonify({
            'id': new_playdate.id,
            'title': new_playdate.title,
            'sport_id': new_playdate.sport_id,
            'creator_id': new_playdate.creator_id,
            'address': new_playdate.address,
            'longitude': new_playdate.longitude,
            'latitude': new_playdate.latitude,
            'date': new_playdate.date.isoformat(),
            'max_participants': new_playdate.max_participants
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Endpoint to get all playdates
@app.route('/playdates', methods=['GET'])
def get_playdates():
    playdates = Playdate.query.all()
    playdates_data = [
        {
            "id": playdate.id,
            "title": playdate.title,
            "sport_id": playdate.sport_id,
            "creator_id": playdate.creator_id,
            "address": playdate.address,
            "latitude": playdate.latitude,
            "longitude": playdate.longitude,
            "date": playdate.date,
            "max_participants": playdate.max_participants
        } for playdate in playdates
    ]
    return jsonify(playdates_data)


# Endpoint to get a specific playdate by ID
@app.route('/playdates/<int:playdate_id>', methods=['GET'])
def get_playdate(playdate_id):
    playdate = data_manager.get_playdate_by_id(playdate_id)
    if playdate:
        playdate_data = {
            "id": playdate.id,
            "title": playdate.title,
            "sport_id": playdate.sport_id,
            "creator_id": playdate.creator_id,
            "address": playdate.address,
            "latitude": playdate.latitude,
            "longitude": playdate.longitude,
            "date": playdate.date,
            "max_participants": playdate.max_participants
        }
        return jsonify(playdate_data)
    return jsonify({"message": "Playdate not found!"}), 404


# Endpoint to add a sport_interest
@app.route('/sport_interest', methods=['POST'])
def add_sport_interest(sport_id):
    data = request.get_json()
    user_id = data.get('user_id')

    user = data_manager.get_user_by_id(user_id)
    sport = data_manager.get_sport_by_id(sport_id)

    if user and sport:
        data_manager.add_sport_interest(user_id=user.id, sport_id=sport.id)
        return jsonify({"message": "User added a sport interest!"}), 201
    return jsonify({"message": "User or sport not found!"}), 404


# Endpoint to get the sport interest
@app.route('/sport_interest', methods=['GET'])
def get_sport_interest():
    """Fetch all sport interests."""
    sport_interest = data_manager.get_all_sport_interest()
    if sport_interest:
        sport_interest_data = {
            "id": sport_interest.id,
            "sport_id": sport_interest.sport_id,
            "user_id": sport_interest.creator_id,
        }
        return jsonify(sport_interest_data)
    return jsonify({"message": "Sport Interest not found!"}), 404


# Endpoint to add a participant to a playdate
@app.route('/playdates/<int:playdate_id>/participants', methods=['POST'])
def add_participant(playdate_id):
    data = request.get_json()
    user_id = data.get('user_id')

    user = data_manager.get_user_by_id(user_id)
    playdate = data_manager.get_playdate_by_id(playdate_id)

    if user and playdate:
        data_manager.add_participant(user_id=user.id, playdate_id=playdate.id)
        return jsonify({"message": "User added as a participant!"}), 201
    return jsonify({"message": "User or playdate not found!"}), 404


# Endpoint to remove a participant from a playdate
@app.route('/playdates/<int:playdate_id>/participants', methods=['DELETE'])
def remove_participant(playdate_id):
    data = request.get_json()
    user_id = data.get('user_id')

    user = data_manager.get_user_by_id(user_id)
    playdate = data_manager.get_playdate_by_id(playdate_id)

    if user and playdate:
        data_manager.remove_participant(user_id=user.id, playdate_id=playdate.id)
        return jsonify({"message": "User removed from participants!"}), 200
    return jsonify({"message": "User or playdate not found!"}), 404


if __name__ == '__main__':
    app.run(debug=True)
