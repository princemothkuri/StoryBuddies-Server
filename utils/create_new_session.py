from bson import ObjectId
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user import add_session_to_user, delete_session_from_user
from models.messages import delete_conversations

# Function to create a new chat session
def create_new_session(user_id, user_prompt):
    session_id = ObjectId()
    add_session_to_user(user_id, session_id, user_prompt)
    return session_id

# Function to delete a session and its messages
def delete_session_id_and_conversations(userId, session_id):
    delete_session_from_user(user_id=userId,session_id=session_id)
    delete_conversations(user_id=userId, session_id=session_id)
    return "Session deleted successfully"
