from flask import Blueprint, request, jsonify
from utils.auth import verify_token

protected_bp = Blueprint('protected', __name__)

def token_required(f):
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 403
        username = verify_token(token)
        if not username:
            return jsonify({'message': 'Invalid or expired token'}), 403
        request.username = username
        return f(*args, **kwargs)
    return decorator

@protected_bp.route('/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({'message': f'Hello, {request.username}! This is a protected route.'})
