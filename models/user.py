from pymongo import MongoClient
from bson import ObjectId
from .messages import get_object_id
from utils.hash_passwords import hash_password
import re
import os
from dotenv import load_dotenv
load_dotenv()

# Use the environment variable for MongoDB URI
MONGO_URI = os.getenv('MONGO_URI')

# Connect to MongoDB using the URI
client = MongoClient(MONGO_URI)
db = client['Interactive_AI_Story_Generation']
users_collection = db['users']

def is_valid_email(email):
    # Regex pattern for validating an email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def is_valid_gender(gender):
    # Valid genders
    valid_genders = ['male', 'female', 'other']
    return gender.lower() in valid_genders

def create_user(username, email, password, gender):
    # Validate email
    if not is_valid_email(email):
        return {"error": "Invalid email address"}
    
    # Validate gender
    if not is_valid_gender(gender):
        return {"error": "Invalid gender. Choose from 'male', 'female', or 'other'."}
    
    # Create a new user with the provided details
    user = {
        'username': username,
        'email': email,
        'password': password,
        'gender': gender.lower(),  
        'sessions': []  
    }
    
    # Insert the user into the MongoDB collection
    users_collection.insert_one(user)
    return {"success": "User created successfully"}

def get_user(username):
    if not is_valid_email(username): 
        return users_collection.find_one({'username': username})
    else:
        return users_collection.find_one({'email': username})

def verify_email(email):
    if not is_valid_email(email): 
        user = users_collection.find_one({'email': email})
        if user:
            return True
        return False
    else:
        return "Invalid Email!"
    
def reset_password(email, new_password):
    print("ok")
    # Check if the email exists in the database
    user = users_collection.find_one({'email': email})
    if not user:
        return {"error": "No user found with that email address."}
    # Hash the new password
    hashed_password = hash_password(new_password)
    
    # Update the user's password in the database
    users_collection.update_one(
        {'_id': user['_id']},
        {'$set': {'password': hashed_password}}
    )
    
    return {"success": "Password has been reset successfully."}

def add_session_to_user(user_id, session_id, user_prompt):
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$push': {'sessions': {"session_id": session_id, "user_prompt": user_prompt}}}
    )

def get_user_sessions(user_id):
    user = users_collection.find_one({'_id': user_id})
    return user.get('sessions', [])

def delete_session_from_user(user_id, session_id):
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$pull': {'sessions': {'session_id': ObjectId(session_id)}}}
    )

def has_session(user_id, session_id):
    if not get_object_id(user_id):
        user_id = ObjectId(user_id)
    if not get_object_id(session_id):
        session_id = ObjectId(session_id)
    
    # Fetch the user document
    user = users_collection.find_one({'_id': user_id})
    
    # Check if session_id is in the user's sessions
    if user:
        sessions = user.get('sessions', [])
        for session in sessions:
            if session.get('session_id') == session_id:
                return True
    
    return False

def get_user_profile(user_id):
    user_id = ObjectId(user_id) if not get_object_id(user_id) else user_id

    # Fetch the user profile
    user = users_collection.find_one(
        {'_id': user_id},
        {'username': 1, 'email': 1, 'gender': 1, '_id': 0}  # Exclude the `_id` field in the output
    )

    
    if user:
        return {"profile": user}
    else:
        return {"error": "User not found"}

def update_user_profile(user_id, username=None, email=None, gender=None):
    user_id = ObjectId(user_id) if not get_object_id(user_id) else user_id

    update_fields = {}

    # Validate and update email if provided
    if email:
        if not is_valid_email(email):
            return {"error": "Invalid email address"}
        update_fields['email'] = email
    
    # Validate and update gender if provided
    if gender:
        if not is_valid_gender(gender):
            return {"error": "Invalid gender. Choose from 'male', 'female', or 'other'."}
        update_fields['gender'] = gender.lower()

    # Update username if provided
    if username:
        update_fields['username'] = username
    
    # Check if there are fields to update
    if not update_fields:
        return {"error": "No valid fields provided for update"}

    # Perform the update
    result = users_collection.update_one(
        {'_id': user_id},
        {'$set': update_fields}
    )
    
    if result.modified_count > 0:
        return {"success": "User profile updated successfully"}
    else:
        return {"error": "User profile update failed or no changes were made"}
