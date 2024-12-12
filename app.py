import os
import secrets
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt

from models import User, Playdate, db, Sport, SportInterest, SportType, Participant
from sqlite_data import SQLiteSportBuddyDataManager

load_dotenv()

app = Flask(__name__)
migrate = Migrate(app, db)

# Configuring SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "data", "sport_buddy.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up JWT configuration
app.config["JWT_SECRET_KEY"] = secrets.token_hex(32)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['JWT_BLACKLIST_ENABLED'] = True
jwt = JWTManager(app)

# Initialize SQLAlchemy
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

data_manager = SQLiteSportBuddyDataManager(db)

revoked_tokens = set()


@app.route('/')
def home():
    return "Welcome to the Sport Buddy!"


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

    user = User.query.get(user_id)
    sport = Sport.query.get(sport_id)

    if not user or not sport:
        return jsonify({"error": "User or sport not found!"}), 404

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

    user = User.query.get(user_id)
    playdate = Playdate.query.get(playdate_id)

    if not user or not playdate:
        return jsonify({"message": "User or playdate not found!"}), 404

    participant = Participant.query.filter_by(user_id=user.id, playdate_id=playdate.id).first()
    if not participant:
        return jsonify({"message": "User is not a participant in this playdate!"}), 404

    try:
        db.session.delete(participant)
        db.session.commit()

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


@app.route('/users/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
    user = data_manager.get_user_by_id(user_id)

    if user:
        try:
            data_manager.remove_user(user_id)
            return jsonify({"message": "User deleted successfully!"}), 200
        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    return jsonify({"message": "User not found!"}), 404


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()

    user = data_manager.get_user_by_id(user_id)
    if not user:
        return jsonify({"message": "User not found!"}), 404

    user.username = data.get('username', user.username)
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)
    user.password = data.get('password', user.password)

    try:
        db.session.commit()
        return jsonify({"message": "User updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/sports/<int:sport_id>', methods=['DELETE'])
def delete_sport(sport_id):
    sport = data_manager.get_sport_by_id(sport_id)

    if sport:
        try:
            db.session.delete(sport)
            db.session.commit()
            return jsonify({"message": "Sport deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    return jsonify({"message": "Sport not found!"}), 404


@app.route('/sports/<int:sport_id>', methods=['PUT'])
def update_sport(sport_id):
    data = request.get_json()

    sport = data_manager.get_sport_by_id(sport_id)
    if not sport:
        return jsonify({"message": "Sport not found!"}), 404

    sport.sport_name = data.get('sport_name', sport.sport_name)
    if 'sport_type' in data and data['sport_type'] in [e.value for e in SportType]:
        sport.sport_type = SportType[data['sport_type'].upper()]

    try:
        db.session.commit()
        return jsonify({"message": "Sport updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/playdates/<int:playdate_id>', methods=['DELETE'])
def delete_playdate(playdate_id):
    playdate = data_manager.get_playdate_by_id(playdate_id)

    if playdate:
        try:
            db.session.delete(playdate)
            db.session.commit()
            return jsonify({"message": "Playdate deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    return jsonify({"message": "Playdate not found!"}), 404


@app.route('/playdates/<int:playdate_id>', methods=['PUT'])
def update_playdate(playdate_id):
    data = request.get_json()

    if not all(k in data for k in ('title', 'sport_id', 'address', 'date', 'max_participants')):
        return jsonify({'error': 'Missing required fields'}), 400

    playdate = data_manager.get_playdate_by_id(playdate_id)
    if not playdate:
        return jsonify({"message": "Playdate not found!"}), 404

    latitude, longitude = data_manager.get_location_coordinates(data['address'])
    if latitude is None or longitude is None:
        return jsonify({'error': 'Unable to fetch coordinates for the new address'}), 400

    playdate.title = data.get('title', playdate.title)
    playdate.sport_id = data.get('sport_id', playdate.sport_id)
    playdate.creator_id = data.get('creator_id', playdate.creator_id)
    playdate.address = data.get('address', playdate.address)
    playdate.date = datetime.strptime(data.get('date', playdate.date.strftime('%d-%m-%Y %H:%M:%S')),
                                      '%d-%m-%Y %H:%M:%S')
    playdate.max_participants = data.get('max_participants', playdate.max_participants)

    try:
        db.session.commit()
        return jsonify({
            'id': playdate.id,
            'title': playdate.title,
            'sport_id': playdate.sport_id,
            'address': playdate.address,
            'latitude': playdate.latitude,
            'longitude': playdate.longitude,
            'date': playdate.date.strftime('%Y-%m-%d %H:%M:%S'),
            'max_participants': playdate.max_participants
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not all(key in data for key in ('email', 'password')):
        return jsonify({"error": "Missing 'email' or 'password'"}), 400

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and user.password == password:
        identity = f"{user.username}"
        access_token = create_access_token(identity=identity)
        return jsonify({"access_token": access_token}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(msg=f"Hello {current_user}, you are logged in!")


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    """Check if a token is in the list of revoked tokens."""
    jti = jwt_payload['jti']
    return jti in revoked_tokens


@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Log out the user by revoking the JWT token."""
    jti = get_jwt()['jti']
    revoked_tokens.add(jti)
    return jsonify({"message": "Successfully logged out!"}), 200


if __name__ == '__main__':
    app.run(debug=True)
