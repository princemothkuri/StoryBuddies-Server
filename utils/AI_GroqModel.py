from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from bson import ObjectId
import json
import sys
from dotenv import load_dotenv
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from models.messages import store_message, messages_collection
from .create_new_session import create_new_session


groq_api_key = os.getenv("GROQ_API_KEY")
model = ChatGroq(
    temperature=0,
    model="llama3-70b-8192",
    api_key=groq_api_key,
    verbose=True,
)

def get_messages_by_user_and_session(user_id, session_id):
    
    cursor = messages_collection.find({
        'user_id': user_id,
        'session_id': ObjectId(session_id)
    }).sort('created_at', 1)

    history = []
    for doc in cursor:
        for message in doc['messages']:
            if message['sender'] == 'human':
                history.append(HumanMessage(content=message['content']))
            elif message['sender'] == 'ai':
                history.append(AIMessage(content=message['content']))
    
    return history

def get_chat_history(session_id):
    
    cursor = messages_collection.find({
        'session_id': ObjectId(session_id)
    }).sort('created_at', 1)

    history = []
    for doc in cursor:
        for message in doc['messages']:
            if message['sender'] == 'human':
                history.append(HumanMessage(content=message['content']))
            elif message['sender'] == 'ai':
                history.append(AIMessage(content=message['content']))
    
    return history


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    history = get_chat_history(session_id)
    return InMemoryChatMessageHistory(messages=history)

def sendMessage(session_id, user_id, user_prompt, original_user_prompt):
    if not session_id:
        session_id = create_new_session(user_id, user_prompt=original_user_prompt)
    history = get_session_history(session_id)
    with_message_history = RunnableWithMessageHistory(model, get_session_history)
    response_from_ai = with_message_history.invoke([HumanMessage(content=user_prompt)], 
                                            config={"configurable": {"session_id": ObjectId(session_id)}})
    response = json.loads(response_from_ai.content)
    human_message = {'sender': 'human', 'content': response['title']}
    ai_message = {'sender': 'ai', 'content': response['story']}
    messages = [human_message, ai_message]
    doc = store_message(session_id, user_id, messages)
    return doc
