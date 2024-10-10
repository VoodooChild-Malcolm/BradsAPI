from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_cors import CORS
app = Flask(__name__)

CORS(app)

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

if __name__ == '__main__':
    app.run(debug=True)
