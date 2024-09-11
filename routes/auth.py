from flask import Blueprint, request, jsonify
from models.user import create_user, get_user, get_user_profile,verify_email,reset_password
from utils.auth import create_token, verify_token
from utils.hash_passwords import hash_password, check_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = hash_password(data['password'])
    gender = data['gender']
    email = data['email']
    create_user(username,email, password, gender)
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    user = get_user(username)
    if user and check_password(user['password'],password):
        token = create_token(user['_id'])
        return jsonify({"token": token, "username": user['username'], "user_id": str(user["_id"])}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route('/verify-email', methods=['POST'])
def verifyEmail():
    data = request.json
    if data:
        res = verify_email(data['email'])
        return jsonify({"user": res}), 200
    return jsonify({"message": "Invalid Email!"}), 401

@auth_bp.route('/reset-password', methods=['POST'])
def resetPassword():
    data = request.json
    if data:
        payload=data['email']
        email = payload['email']
        new_password=payload['password']
        try:
            res = reset_password(email=email,new_password=new_password)
            return jsonify(res), 200
        except:
            return jsonify({"message": "Server error"}), 401
    return jsonify({"message": "Server error"}), 401


@auth_bp.route('/profile', methods=['POST'])
def profile():
    data = request.json
    if 'token' in data:
        user_id = verify_token(data['token'])
        if user_id is None:
            return jsonify({"message": "Invalid login. Please log in again."}), 400
        else:
            try:
                res = get_user_profile(user_id=user_id)
                return jsonify(res), 200
            except Exception as e:
                return jsonify({"message": f"Unfortunately, an error has occurred, unable to fetch the profile. Error: {e}"}), 400
    else:
        return jsonify({"message": "No Token provided"}), 400
