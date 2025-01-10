# **Sport Buddy App Backend**

Welcome to the backend of the Sport Buddy App! This app connects users who share a love for sports, allowing them to find playdates, connect with others, and join sport events.

### **Features**

	•	User Management: Users can register, view, and update their profiles.
	•	Sports: Add and view various sports available for playdates.
	•	Playdates: Create and join playdates based on your favorite sports.
	•	Sport Interests: Users can express their interest in different sports.
	•	Participants: Users can join or leave playdates, and track participants for each event.

### **Setup**

#### **Requirements**

	•	Python 3.7 or higher
	•	Flask
	•	SQLAlchemy
	•	Flask-CORS
	•	Flask-JWT-Extended
	•	Flask-Migrate
	•	dotenv (for environment variables)
    •	Mapbox (for geolocation)

#### **Installation**

	1.	Clone the repository:
    ```
    git clone https://github.com/your-username/sport-buddy-backend.git
    ```
    2. 	Navigate to the project directory:
    ```
    cd sport-buddy-backend
    ```
    3. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
    4. Create a .env file in the project root and add the necessary environment variables:
    ```
    JWT_SECRET_KEY=your-secret-key
    MAPBOX_API_KEY=your-mapbox-api-key
    ```

#### **Running the App**

To run the application locally, execute the following command:
    ```
    flask run
    ```
The backend will be available at http://127.0.0.1:5000.

##### **Database Setup**

The backend uses SQLite for data storage. On the first run, the app will create the necessary database tables automatically.

To initialize the database, run:
    ```
    flask db init
    flask db migrate
    flask db upgrade
    ```

#### **Endpoints**

##### User Management

	•	POST /users: Create a new user
	•	GET /users: Get a list of all users
	•	GET /users/{user_id}: Get a user’s profile by ID
	•	PUT /users/{user_id}: Update a user’s profile
	•	DELETE /users/{user_id}: Delete a user

##### **Sports**

	•	POST /sports: Add a new sport
	•	GET /sports: Get a list of all sports

##### **Playdates**

	•	POST /playdates: Create a new playdate
	•	GET /playdates: Get a list of all playdates
	•	GET /playdates/{playdate_id}: Get details of a playdate by ID
	•	POST /playdates/{playdate_id}/participants: Add a user as a participant to a playdate
	•	DELETE /playdates/{playdate_id}/participants: Remove a user from a playdate
	•	GET /playdates/{playdate_id}/participants: Get participants of a playdate

##### **Sport Interests**

	•	POST /sport_interest: Add a sport interest for a user
	•	GET /sport_interest: Get a list of all sport interests

#### **Mapbox Integration**

The app uses Mapbox to handle geolocation data for playdate locations. To enable Mapbox functionality, you need to provide your Mapbox API key in the .env file:
    ```
    MAPBOX_API_KEY=your-mapbox-api-key
    ```
When creating a playdate, the app will use Mapbox to convert addresses into geographic coordinates (latitude and longitude).

#### **Deployment**

The backend has been deployed to Render, and it is accessible at:

https://sport-buddy-test.onrender.com

#### **Authentication**

This app uses JWT for authentication. To access most endpoints, you will need to pass a valid JWT token in the request headers.
	•	POST /login: To authenticate and receive a token.

**Example:**
    ```
    curl -X POST http://127.0.0.1:5000/login -d '{"username": "your-username", "password": "your-password"}'
    ```

The response will include the JWT token:
    ```
    {
    "access_token": "your-access-token"
    }
    ```
Include this token in the Authorization header of subsequent requests:
    ```
    curl -X GET http://127.0.0.1:5000/users -H "Authorization: Bearer your-access-token"
    ```

#### **License**

This project is licensed under the MIT License - see the LICENSE file for details.