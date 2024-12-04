import os
from datetime import datetime
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from models import User, Playdate, db, Sport, SportInterest, SportType, Participant
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

    required_fields = ('username', 'first_name', 'last_name', 'email', 'password')
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({'error': 'Missing or empty required fields'}), 400

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

    if not data.get('sport_name'):
        return jsonify({'error': 'Sport name is required'}), 400
    if 'sport_type' in data and data['sport_type'] not in [e.value for e in SportType]:
        return jsonify({'error': 'Invalid sport type'}), 400

    try:
        sport_type = SportType[data['sport_type'].upper()] if 'sport_type' in data else SportType.BOTH

        new_sport = Sport(
            sport_name=data['sport_name'],
            sport_type=sport_type
        )

        db.session.add(new_sport)
        db.session.commit()

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
    users_data = [{"id": user.id, "username": user.username, "first_name": user.first_name, "last_name": user.last_name}
                  for user in users]
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
    if not all(k in data for k in ('title', 'sport_id', 'creator_id', 'address', 'date')):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        latitude, longitude = data_manager.get_location_coordinates(data['address'])
        if latitude is None or longitude is None:
            return jsonify({'error': 'Unable to fetch coordinates for the address'}), 400
        # Parse the 'date' string to a Python datetime object
        playdate_date = datetime.strptime(data['date'], '%d-%m-%Y %H:%M:%S')

        # Create a new playdate
        new_playdate = Playdate(
            title=data['title'],
            sport_id=data['sport_id'],
            creator_id=data['creator_id'],
            address=data['address'],
            longitude=longitude,
            latitude=latitude,
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
def add_sport_interest():
    data = request.get_json()

    if not data or not all(key in data for key in ('user_id', 'sport_id')):
        return jsonify({"error": "Missing required fields: 'user_id' and/or 'sport_id'"}), 400

    user_id = data.get('user_id')
    sport_id = data.get('sport_id')

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
    sport_interests = SportInterest.query.all()
    if sport_interests:
        sport_interest_data = [
            {
                "id": sport_interest.id,
                "sport_id": sport_interest.sport_id,
                "user_id": sport_interest.user_id,
            } for sport_interest in sport_interests
        ]
        return jsonify(sport_interest_data)
    return jsonify({"message": "Sport Interest not found!"}), 404


# Endpoint to add a participant to a playdate
@app.route('/playdates/<int:playdate_id>/participants', methods=['POST'])
def add_participant(playdate_id):
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"message": "Missing 'user_id' in request data!"}), 400

    # Fetch user and playdate from the database
    user = User.query.get(user_id)
    playdate = Playdate.query.get(playdate_id)

    if not user:
        return jsonify({"message": f"User with ID {user_id} not found!"}), 404
    if not playdate:
        return jsonify({"message": f"Playdate with ID {playdate_id} not found!"}), 404

    existing_participant = Participant.query.filter_by(user_id=user.id, playdate_id=playdate.id).first()
    if existing_participant:
        return jsonify({"message": "User is already a participant!"}), 409

    current_participants = len(playdate.participants)
    if playdate.max_participants and current_participants >= playdate.max_participants:
        return jsonify({"message": "Playdate has reached its maximum capacity!"}), 403

    try:
        new_participant = Participant(user_id=user.id, playdate_id=playdate.id)
        db.session.add(new_participant)
        db.session.commit()

        updated_playdate = Playdate.query.get(playdate_id)
        updated_participants_count = len(updated_playdate.participants)

        print(f"Playdate ID {playdate_id} now has {updated_participants_count} participants.")
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

    # Serialize the Playdate object
    playdate_dict = {
        "id": updated_playdate.id,
        "title": updated_playdate.title,
        "date": updated_playdate.date.strftime('%Y-%m-%d %H:%M:%S') if updated_playdate.date else None,
        "max_participants": updated_playdate.max_participants,
        "participants_count": updated_participants_count,
        "participants": [
            {"id": participant.user_id, "username": User.query.get(participant.user_id).username}
            # Fetch user by user_id
            for participant in updated_playdate.participants
        ]
    }

    return jsonify({
        "message": "User added as a participant!",
        "playdate": playdate_dict,
        "participants_count": updated_participants_count
    }), 201


# Endpoint to remove a participant from a playdate
@app.route('/playdates/<int:playdate_id>/participants', methods=['DELETE'])
def remove_participant(playdate_id):
    data = request.get_json()
    user_id = data.get('user_id')

    # Fetch user and playdate from the database
    user = User.query.get(user_id)
    playdate = Playdate.query.get(playdate_id)

    # Check if both the user and the playdate exist
    if not user or not playdate:
        return jsonify({"message": "User or playdate not found!"}), 404

    # Check if the user is already a participant in the playdate
    participant = Participant.query.filter_by(user_id=user.id, playdate_id=playdate.id).first()
    if not participant:
        return jsonify({"message": "User is not a participant in this playdate!"}), 404

    # Remove the participant from the playdate
    try:
        db.session.delete(participant)
        db.session.commit()

        # Refresh playdate to get the updated participant list and count
        updated_playdate = Playdate.query.get(playdate_id)
        updated_participants_count = len(updated_playdate.participants)

        # Serialize the updated playdate data
        playdate_dict = {
            "id": updated_playdate.id,
            "title": updated_playdate.title,
            "date": updated_playdate.date.strftime('%Y-%m-%d %H:%M:%S') if updated_playdate.date else None,
            "max_participants": updated_playdate.max_participants,
            "participants_count": updated_participants_count,
            "participants": [
                {"id": participant.user_id, "username": User.query.get(participant.user_id).username}
                for participant in updated_playdate.participants
            ]
        }

        return jsonify({
            "message": "User removed from participants!",
            "playdate": playdate_dict,
            "participants_count": updated_participants_count
        }), 200

    except Exception as e:
        db.session.rollback()  # In case of an error, rollback the transaction
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


@app.route('/playdates/<int:playdate_id>/participants', methods=['GET'])
def get_participants(playdate_id):
    playdate = Playdate.query.get(playdate_id)

    if not playdate:
        return jsonify({"message": "Playdate not found!"}), 404

    participants = Participant.query.filter_by(playdate_id=playdate_id).all()

    if not participants:
        return jsonify({"message": "No participants found for this playdate!"}), 404

    # Serialize the participant data
    participants_list = [
        {
            "id": participant.user_id,
            "username": User.query.get(participant.user_id).username
        }
        for participant in participants
    ]

    return jsonify({
        "playdate_id": playdate_id,
        "title": playdate.title,
        "max_participants": playdate.max_participants,
        "participants_count": len(participants_list),
        "participants": participants_list
    }), 200


if __name__ == '__main__':
    app.run(debug=True)
