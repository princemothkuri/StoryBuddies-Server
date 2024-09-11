import jwt
from flask import current_app as app

def create_token(user_id):
    token = jwt.encode({
        'user_id': str(user_id)  
    }, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_token(token):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return data['user_id']  
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
