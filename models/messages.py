from pymongo import MongoClient
from bson import ObjectId
import datetime
from pymongo import DESCENDING, ASCENDING
import os
from dotenv import load_dotenv
load_dotenv()

# Use the environment variable for MongoDB URI
MONGO_URI = os.getenv('MONGO_URI')

# Connect to MongoDB using the URI
client = MongoClient(MONGO_URI)
db = client['Interactive_AI_Story_Generation']
messages_collection = db['messages']
users_collection = db['users']

def get_object_id(oid):
    # Check if the input is already an ObjectId instance
    if isinstance(oid, ObjectId):
        return True  # It's already an ObjectId, proceed with it
    return False

def convert_object_id_to_string(oid):
    # Convert ObjectId to string if it's an ObjectId
    if get_object_id(oid):
        return str(oid)
    return oid

def store_message(session_id, user_id, messages):
    # Convert session_id to ObjectId if it's not already an ObjectId
    session_id = ObjectId(session_id) if not get_object_id(session_id) else session_id
    
    res = messages_collection.insert_one({
        'session_id': session_id,
        'user_id': user_id,
        'messages': messages,
        'upvotes': [],
        'downvotes': [],
        'created_at': datetime.datetime.now(datetime.timezone.utc)
    })

    # Fetch the inserted document using the inserted_id
    inserted_id = res.inserted_id
    document = messages_collection.find_one({'_id': inserted_id})

    # Convert ObjectId fields to strings
    if document:
        document['_id'] = str(document['_id'])
        document['session_id'] = str(document['session_id'])

        # Remove messages array and extract title and story
        if document['messages']:
            document['title'] = document['messages'][0]['content']
            document['story'] = document['messages'][1]['content']
            del document['messages']  # Remove the messages array
            del document['user_id']

    return document

# messages = [
#     {'sender': 'human', 'content': 'Hello, AI!'},
#     {'sender': 'AI', 'content': 'Hello, human! How can I assist you today?'}
# ]

def delete_conversations(user_id, session_id):
    
    if not get_object_id(session_id):
        session_id = ObjectId(session_id)
    
    # Delete all documents that match both user_id and session_id
    messages_collection.delete_many({
        'user_id': convert_object_id_to_string(user_id),
        'session_id': session_id
    })
    


def upvote_message(user_id, message_id):
    # Convert to ObjectId if needed
    if not get_object_id(message_id):
        message_id = ObjectId(message_id)
    if not get_object_id(user_id):
        user_id = ObjectId(user_id)
    
    # Check if the user has already upvoted the message
    message = messages_collection.find_one(
        {'_id': message_id}
    )
    
    if user_id in message.get('upvotes', []):
        # User has already upvoted the message, remove the upvote
        messages_collection.update_one(
            {'_id': message_id},
            {'$pull': {'upvotes': user_id}}
        )
        return "Upvote removed"
    
    # Remove user from downvotes if present
    messages_collection.update_one(
        {'_id': message_id},
        {'$pull': {'downvotes': user_id}}
    )
    
    # Add user to upvotes
    messages_collection.update_one(
        {'_id': message_id},
        {'$addToSet': {'upvotes': user_id}}
    )
    
    return "Upvote added"

def downvote_message( user_id, message_id):
    # Convert to ObjectId if needed
    if not get_object_id(message_id):
        message_id = ObjectId(message_id)
    if not get_object_id(user_id):
        user_id = ObjectId(user_id)
    
    # Check if the user has already downvoted the message
    message = messages_collection.find_one(
        {'_id': message_id}
    )
    
    if user_id in message.get('downvotes', []):
        # User has already downvoted the message, remove the downvote
        messages_collection.update_one(
            {'_id': message_id},
            {'$pull': {'downvotes': user_id}}
        )
        return "Downvote removed"
    
    # Remove user from upvotes if present
    messages_collection.update_one(
        {'_id': message_id},
        {'$pull': {'upvotes': user_id}}
    )
    
    # Add user to downvotes
    messages_collection.update_one(
        {'_id': message_id},
        {'$addToSet': {'downvotes': user_id}}
    )
    
    return "Downvote added"

def pagination_leaderboard(skip, per_page):
    # Fetch stories sorted by upvotes (descending) and then by creation time (most recent first)
    stories = messages_collection.find() \
        .sort([('upvotes', DESCENDING), ('created_at', DESCENDING)]) \
        .skip(skip) \
        .limit(per_page)

    results = []
    for story in stories:
        results.append({
            "_id": str(story['_id']),
            'session_id': str(story['session_id']),
            
            'upvotes': len(story.get('upvotes', [])),
            'downvotes': len(story.get('downvotes', [])),
            'title': story['messages'][0].get('content',''),
            'story':story['messages'][1].get('content',''),
            
            'created_at': story['created_at'].isoformat()
        })

    return results

def fetch_messages_by_session(session_id):
    # Convert session_id to ObjectId if it's not already
    session_id = ObjectId(session_id) if not get_object_id(session_id) else session_id
    
    # Fetch user prompt from the user's sessions
    user_doc = users_collection.find_one({'sessions.session_id': session_id})
    if user_doc:
        user_prompt = next((session['user_prompt'] for session in user_doc['sessions'] if str(session['session_id']) == str(session_id)), None)
    else:
        user_prompt = None
    
    # Fetch messages for the given session_id
    messages = messages_collection.find({'session_id': session_id}).sort('created_at', ASCENDING)
    
    stories = []
    
    for message in messages:
        # Convert ObjectId values in upvotes and downvotes to strings
        upvotes = [str(vote) for vote in message.get('upvotes', [])]
        downvotes = [str(vote) for vote in message.get('downvotes', [])]
        
        story = {
            '_id': str(message['_id']),
            'upvotes': upvotes,
            'downvotes': downvotes,
            'title': message['messages'][0].get('content', ''),
            'story': message['messages'][1].get('content', '')
        }
        stories.append(story)
    return {
        'user_prompt': user_prompt,
        'stories': stories
    }

def fetch_first_message_of_each_session(user_id):
    user_id = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id

    # Fetch all sessions of the current user
    user_doc = users_collection.find_one({'_id': user_id}, {'sessions': 1})
    if not user_doc or 'sessions' not in user_doc:
        return {"message": "No sessions found for this user."}

    sessions = user_doc['sessions']

    stories = []

    # Iterate through each session and fetch the first message
    for session in sessions:
        session_id = session['session_id']
        user_prompt = session.get('user_prompt', '')
        
        # Fetch the first message of the session
        message_doc = messages_collection.find_one(
            {'session_id': ObjectId(session_id)},
            sort=[('created_at', DESCENDING)],
            
        )
        if message_doc and 'messages' in message_doc and len(message_doc['messages']) > 0:
            story = {
                '_id': str(message_doc['_id']),
                'upvotes': len(message_doc.get('upvotes', [])),
                'downvotes': len(message_doc.get('downvotes', [])),
                'title': message_doc['messages'][0].get('content',''), 
                'story': message_doc['messages'][1].get('content',''),
                'session_id': str(session_id),
                'user_prompt': user_prompt,
                "created_at": message_doc['created_at']
            }
            
            stories.append(story)

    # Sort the stories list by created_at in descending order
    stories.sort(key=lambda x: x['created_at'], reverse=True)
    return {'stories': stories}

def get_featured_stories():
    # Fetch the latest 3 stories
    new_stories = list(messages_collection.find().sort("created_at", -1).limit(3))
    
    # Fetch the top 3 upvoted stories
    upvoted_stories = list(messages_collection.aggregate([
        {"$addFields": {"upvote_count": {"$size": "$upvotes"}}},
        {"$sort": {"upvote_count": -1}},
        {"$limit": 3}
    ]))

    stories = []
    seen_ids = set()

    for msg in upvoted_stories:
        story_id = str(msg['_id'])
        if story_id not in seen_ids:
            story = {
                "_id": story_id,
                "user_id": str(msg['user_id']),
                "session_id": str(msg['session_id']),
                'title': msg['messages'][0].get('content', ''),
                'story': msg['messages'][1].get('content', '')
            }
            stories.append(story)
            seen_ids.add(story_id)

    for msg in new_stories:
        story_id = str(msg['_id'])
        if story_id not in seen_ids:
            story = {
                "_id": story_id,
                "user_id": str(msg['user_id']),
                "session_id": str(msg['session_id']),
                'title': msg['messages'][0].get('content', ''),
                'story': msg['messages'][1].get('content', '')
            }
            stories.append(story)
            seen_ids.add(story_id)

    return stories
