from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user import has_session
from models.messages import downvote_message, upvote_message, pagination_leaderboard, fetch_messages_by_session, fetch_first_message_of_each_session, get_featured_stories
from utils.auth import verify_token
from utils.create_new_session import  delete_session_id_and_conversations
from utils.AI_GroqModel import sendMessage

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/delete_session', methods=['DELETE'])
def create_session():
    data = request.json
    if 'token' in data:
        user_id = verify_token(data['token'])
        if user_id is None:
            return jsonify({"message": "Invalid or expired token. Please log in again."}), 400
        else:
            session_id = data['session_id']
            if session_id == "":
                return jsonify({"message": "unfortunately unable to delete."}), 400
            try:
                delete_session_id_and_conversations(userId=user_id,session_id=session_id)
                return jsonify({"message": "Session deleted successfully","session_id": session_id}), 200
            except:
                return jsonify({"message": "unfortunately error has occured, unable to delete the session.","session_id": session_id}), 200

        
    else:
        # Logic when session_id is not provided
        return jsonify({"message": "No Token provided"}), 400

@chat_bp.route('/send_message', methods=['POST'])
def send_message():
    data = request.json

    if 'token' in data:
        user_id = verify_token(data['token'])
        if user_id is None:
            return jsonify({"message": "Invalid or expired token. Please log in again."}), 400
        else:
            tags = data.get('tags', [])
            tags_str = ', '.join(tags)
            session_id = None
            content = f"""User Prompt: {data['content']}  Tags: {tags_str}  **Create a story in 100 words based on the user prompt, tags (tags are representing that how the story should be) and response should be in json format only, use the key 'story' and 'title' give appropriate title for the story which your giving like a title for the episode for the story which your generating. Give episode number in the title. starts from 1**"""
            if data['session_id'] != "":
                session_id = data['session_id']
                content =  f"""User Prompt: " {data['content']} "**Continue the story from where you left in 100 words based on the user prompt and response should be in json format only, use the key 'story' and 'title' give appropriate title for the story which your giving like a title for the episode for the story which your generating. Give episode number in the title. based on the previous episode write the next episode story and change the eposode number i mean increment the number**"""
                if has_session(user_id=user_id,session_id=session_id):
                    doc = sendMessage(session_id=session_id,user_id=user_id,user_prompt=content, original_user_prompt=data['content'])
                    return jsonify({"message": "Message sent successfully", "generatedstory": doc, "user_prompt":data['content'] }), 200
                else:
                    return jsonify({"message": "Unauthorized user!."}), 400
            
            try:
                doc = sendMessage(session_id=session_id,user_id=user_id,user_prompt=content, original_user_prompt=data['content'])
                return jsonify({"message": "Message sent successfully", "generatedstory": doc, "user_prompt":data['content'] }), 200
            except:
                return jsonify({"message": "Error occured while creating new story, please try again after some time."}), 400
    else:
        return jsonify({"message": "No Token provided"}), 400
    

@chat_bp.route('/upvote', methods=['POST'])
def upvote_story():
    data = request.json
    if 'token' in data:
        user_id = verify_token(data['token'])
        if user_id is None:
            return jsonify({"message": "Invalid or expired token. Please log in again."}), 400
        else:
            
            try:
                if data['message_id'] == "":
                    return jsonify({"message": "unfortunately unable to upvote.","message_id": data['message_id']}), 400

                res = upvote_message(user_id=user_id,message_id=data['message_id'])
                return jsonify({"message": res,"message_id": data['message_id']}), 200
            except:
                return jsonify({"message": "unfortunately error has occured, unable to upvote the story.","message_id": data['message_id']}), 200

        
    else:
        return jsonify({"message": "No Token provided"}), 400
    
@chat_bp.route('/downvote', methods=['POST'])
def downvote_story():
    data = request.json
    if 'token' in data:
        user_id = verify_token(data['token'])
        if user_id is None:
            return jsonify({"message": "Invalid login. Please log in again."}), 400
        else:
            try:
                if data['message_id'] == "":
                    return jsonify({"message": "unfortunately unable to downvote.","message_id": data['message_id']}), 400

                res = downvote_message(user_id=user_id,message_id=data['message_id'])
                return jsonify({"message": res,"message_id": data['message_id']}), 200
            except:
                return jsonify({"message": "unfortunately error has occured, unable to upvote the story.","message_id": data['message_id']}), 200

        
    else:
        return jsonify({"message": "No Token provided"}), 400
    
@chat_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    page = int(request.args.get('page', 1))
    per_page = 10

    skip = (page - 1) * per_page

    results = pagination_leaderboard(skip=skip, per_page=per_page)
    return jsonify({"leaderboard": results}), 200

@chat_bp.route('/fetch_total_story_by_using_session', methods=['POST'])
def fetch_total_story_by_using_session():
    data = request.json
    if 'token' in data:
        user_id = verify_token(data['token'])
        if user_id is None:
            return jsonify({"message": "Invalid login. Please log in again."}), 400
        else:
            try:
                res = fetch_messages_by_session(session_id=data['session_id'])
                return jsonify(res), 200
            except:
                return jsonify({"message": "unfortunately error has occured, unable to fetch the story.","session_id": data['session_id']}), 400

        
    else:
        return jsonify({"message": "No Token provided"}), 400
    
@chat_bp.route('/fetch_first_message_of_each_session_of_current_user', methods=['POST'])
def fetch_first_message_of_each_session_of_current_user():
    data = request.json
    if 'token' in data:
        user_id = verify_token(data['token'])
        if user_id is None:
            return jsonify({"message": "Invalid login. Please log in again."}), 400
        else:
            try:
                stories = fetch_first_message_of_each_session(user_id=user_id)
                return jsonify(stories), 200
            except Exception as e:
                return jsonify({"message": f"Unfortunately, an error has occurred, unable to fetch the stories. Error: {e}"}), 400
    else:
        return jsonify({"message": "No Token provided"}), 400

@chat_bp.route('/featured-stories', methods=['POST'])
def featured_stories():
    data = request.json
    if 'token' in data:
        user_id = verify_token(data['token'])
        if user_id is None:
            return jsonify({"message": "Invalid login. Please log in again."}), 400
        else:
            try:
                stories = get_featured_stories()
                return jsonify(stories), 200
            except Exception as e:
                return jsonify({"message": f"Unfortunately, an error has occurred, unable to fetch the stories. Error: {e}"}), 400
    else:
        return jsonify({"message": "No Token provided"}), 400