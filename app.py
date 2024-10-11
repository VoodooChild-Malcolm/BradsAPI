from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
import datetime

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}},
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)


# Configure MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/recipeDB"  # Change this to your MongoDB URI
mongo = PyMongo(app)

# Route to get all recipes
@app.route('/recipes', methods=['GET'])
def get_recipes():
    recipes = mongo.db.recipes.find()
    return dumps(recipes), 200  # Use dumps to convert cursor to JSON

# Route to get a single recipe by ID
@app.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if recipe:
        return dumps(recipe), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404

# Route to add a new recipe
@app.route('/recipes', methods=['POST'])
def add_recipe():
    data = request.get_json()
    if 'name' and 'ingredients' in data:
        recipe_id = mongo.db.recipes.insert_one(data).inserted_id
        return jsonify({"message": "Recipe added", "id": str(recipe_id)}), 201
    else:
        return jsonify({"error": "Invalid data"}), 400

# Route to update a recipe by ID
@app.route('/recipes/<recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    data = request.get_json()
    updated_recipe = mongo.db.recipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$set": data}
    )
    if updated_recipe.matched_count > 0:
        return jsonify({"message": "Recipe updated"}), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404

# Route to delete a recipe by ID
@app.route('/recipes/<recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    result = mongo.db.recipes.delete_one({"_id": ObjectId(recipe_id)})
    if result.deleted_count > 0:
        return jsonify({"message": "Recipe deleted"}), 200
    else:
        return jsonify({"error": "Recipe not found"}), 404


app.config['SECRET_KEY'] = 'your_secret_key'

# Replace with your Google Client ID
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"


# Route to handle Google OAuth login
@app.route('/auth/google', methods=['POST'])
def google_login():
    token = request.json.get('token')

    try:
        # Verify the token using Google API
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        # Extract user information from the token
        user_id = idinfo['sub']  # Google user ID
        email = idinfo.get('email')
        name = idinfo.get('name')

        # Check if the user already exists in the database
        user = mongo.db.users.find_one({'google_id': user_id})

        if user is None:
            # If the user doesn't exist, create a new entry
            new_user = {
                'google_id': user_id,
                'email': email,
                'name': name,
                'created_at': datetime.datetime.utcnow()
            }
            mongo.db.users.insert_one(new_user)
            user = new_user

        # Generate a JWT for the user
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'token': token, 'user': {'name': name, 'email': email}}), 200

    except ValueError as e:
        # Invalid token
        return jsonify({'error': 'Invalid token', 'message': str(e)}), 400


# Route to get user data (protected route)
@app.route('/user', methods=['GET'])
def get_user():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing!'}), 403

    try:
        # Decode JWT token to get user information
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = mongo.db.users.find_one({'google_id': decoded['user_id']})

        if user:
            return jsonify({'user': {'name': user['name'], 'email': user['email']}}), 200
        else:
            return jsonify({'error': 'User not found!'}), 404

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 403
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 403



if __name__ == '__main__':
    app.run(debug=True)
