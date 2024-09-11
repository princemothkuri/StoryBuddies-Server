from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from routes.auth import auth_bp
from routes.chat import chat_bp

import os
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')

    # Initialize MongoDB
    PyMongo(app)

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
