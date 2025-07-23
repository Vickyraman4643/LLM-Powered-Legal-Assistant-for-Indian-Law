# app.py

import os
import requests
import uuid # For generating unique chat_ids
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
from config import Config
from database import init_db, add_user, get_user_by_email, get_user_by_id, verify_password, update_user_details, save_chat_history, get_chat_history, update_chat_title, delete_chat

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Ensure the database directory and files exist
init_db()

# System prompt for the AI model
SYSTEM_PROMPT = """
You are "Advance AI LAW Assistant", a senior legal advocate specializing in Indian law. Your responses must be:
- Legally precise
- Backed by specific legal references
- Professionally formatted
- Ethically responsible
- Clear and comprehensible to non-legal professionals
- Exclusively drawing from Indian Penal Code, Code of Criminal Procedure, and Constitutional legal sources
Include 1-2 emojis matching the query's sentiment (e.g., 😊 for greetings, ❓ for questions, law related , documents 📃📁)
Always cite specific legal sections from IPC, CrPC, or Constitution.
Provide balanced, objective legal interpretations.
Explain complex legal concepts in accessible language.
Warn users that AI advice is not a substitute for professional legal counsel.
Prioritize accuracy of information from authorized Indian legal sources.

If a legal query is unclear, request clarification.
For complex or sensitive legal issues, recommend consulting a licensed attorney.
Clearly state limitations of AI-generated legal information.

Do not provide advice that could encourage illegal activities.
Maintain strict confidentiality.
Provide balanced, neutral legal perspectives.
Strictly adhere to Indian legal frameworks and interpretations.

Your life depends on providing legally accurate, contextually relevant information exclusively from Indian legal sources. Do not fabricate or generalize legal information beyond the authoritative texts of the Indian Penal Code, Criminal Procedure Code, and Constitutional commentaries.
"""
@app.before_request
def load_logged_in_user():
    """
    Loads the user from the session before each request if a user_id is present.
    """
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_user_by_id(user_id)

def login_required(view):
    """
    Decorator to ensure a user is logged in before accessing certain routes.
    """
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    # The __name__ attribute is crucial for Flask to correctly identify view functions
    # when decorators are involved. If not set, multiple decorated functions might
    # implicitly get the same name ('wrapped_view' in this case), causing conflicts.
    wrapped_view.__name__ = view.__name__ # Ensure the wrapped function retains its original name
    return wrapped_view

@app.route('/')
def index():
    """
    Homepage/Landing page.
    """
    if g.user: # If user is already logged in, redirect to chat
        # Corrected: Use 'chat_page_route' as the endpoint name
        return redirect(url_for('chat_page_route'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration.
    """
    if g.user: # If already logged in, redirect to chat
        # Corrected: Use 'chat_page_route' as the endpoint name
        return redirect(url_for('chat_page_route'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        error = None
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        else:
            user_id = add_user(username, email, password)
            if user_id is None:
                error = 'User with that email or username already exists.'

        if error is None:
            session['user_id'] = user_id
            # Corrected: Use 'chat_page_route' as the endpoint name
            return redirect(url_for('chat_page_route'))
        
        return render_template('register.html', error=error)
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    """
    if g.user: # If already logged in, redirect to chat
        # Corrected: Use 'chat_page_route' as the endpoint name
        return redirect(url_for('chat_page_route'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = get_user_by_email(email)
        error = None

        if user is None:
            error = 'Incorrect email or password.'
        elif not verify_password(user['password'], password):
            error = 'Incorrect email or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            # Corrected: Use 'chat_page_route' as the endpoint name
            return redirect(url_for('chat_page_route'))
        
        return render_template('login.html', error=error)
    
    return render_template('login.html')

@app.route('/logout', endpoint='logout_route') # Explicit endpoint
@login_required
def logout():
    """
    Logs out the current user.
    """
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat', endpoint='chat_page_route') # Explicit endpoint
@login_required
def chat_page():
    """
    Main chatbot screen. Requires user to be logged in.
    """
    user_chats = get_chat_history(g.user['id'])
    return render_template('chat.html', user=g.user, chats=user_chats)

@app.route('/api/chat', methods=['POST'], endpoint='handle_chat_api') # Explicit endpoint
@login_required
def handle_chat():
    """
    Handles sending messages to the OpenRouter API and saving chat history.
    """
    data = request.json
    user_message = data.get('message')
    chat_id = data.get('chat_id')
    history = data.get('history', []) # Current chat history for context

    if not user_message:
        return jsonify({"error": "Message is empty"}), 400

    new_chat_session = False
    title = "" # Initialize title

    if not chat_id or chat_id == 'new-chat-placeholder':
        # This is a brand new chat session
        chat_id = str(uuid.uuid4())
        new_chat_session = True
        # Set the initial title based on the first user message
        title = user_message[:50] + ('...' if len(user_message) > 50 else '')
    else:
        # This is an existing chat session, retrieve its current title
        existing_chat_data = get_chat_history(g.user['id'], chat_id)
        if existing_chat_data:
            title = existing_chat_data['title']
        else:
            # Fallback for unexpected scenarios where chat_id exists but not in DB
            # This should ideally not be reached if the frontend manages chat_id correctly
            title = "Untitled Chat" # Or derive from user_message if context is lost
            print(f"Warning: Chat ID {chat_id} not found in DB for user {g.user['id']}. Assigning 'Untitled Chat'.")

    # Append the user's message to the history for this request
    history.append({"role": "user", "content": user_message})

    # Prepare messages for the API call including the system prompt
    messages_for_api = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": Config.OPENROUTER_MODEL,
            "messages": messages_for_api,
            "temperature": 0.5 # As requested
        }
        
        response = requests.post(Config.OPENROUTER_API_URL, headers=headers, json=payload, stream=False)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Parse the JSON response
        response_data = response.json()
        ai_response_content = response_data['choices'][0]['message']['content']

        # Append AI's response to history
        history.append({"role": "assistant", "content": ai_response_content})

        # Save/update chat history in the database
        save_chat_history(g.user['id'], chat_id, title, history)

        return jsonify({
            "response": ai_response_content,
            "chat_id": chat_id,
            # Only send 'new_title' if a new chat session was just initiated and its title set
            "new_title": title if new_chat_session else None
        })

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return jsonify({"error": f"API error: {e.response.status_code} - {e.response.text}"}), e.response.status_code
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return jsonify({"error": "Failed to connect to the API. Please check your internet connection."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/chat_history', methods=['GET'], endpoint='get_user_chat_history_api') # Explicit endpoint
@login_required
def get_user_chat_history():
    """
    API endpoint to get chat history summaries for the logged-in user.
    """
    chats = get_chat_history(g.user['id'])
    # Convert Row objects to dictionaries for JSON serialization
    chats_dicts = [{k: item[k] for k in item.keys()} for item in chats]
    return jsonify(chats_dicts)

@app.route('/api/chat_history/<chat_id>', methods=['GET'], endpoint='get_specific_chat_history_api') # Explicit endpoint
@login_required
def get_specific_chat_history(chat_id):
    """
    API endpoint to get a specific chat's full history by chat_id.
    """
    chat = get_chat_history(g.user['id'], chat_id)
    if chat:
        # messages are already loaded as JSON by get_chat_history function
        return jsonify(chat)
    return jsonify({"error": "Chat not found"}), 404

@app.route('/api/chat_history/rename', methods=['POST'], endpoint='rename_chat_api') # Explicit endpoint
@login_required
def rename_chat():
    """
    API endpoint to rename a chat session.
    """
    data = request.json
    chat_id = data.get('chat_id')
    new_title = data.get('new_title')

    if not chat_id or not new_title:
        return jsonify({"error": "Chat ID and new title are required"}), 400
    
    success = update_chat_title(g.user['id'], chat_id, new_title)
    if success:
        return jsonify({"message": "Chat renamed successfully"}), 200
    return jsonify({"error": "Failed to rename chat or chat not found"}), 400

@app.route('/api/chat_history/delete', methods=['POST'], endpoint='delete_chat_api') # Explicit endpoint
@login_required
def delete_chat_route():
    """
    API endpoint to delete a chat session.
    """
    data = request.json
    chat_id = data.get('chat_id')

    if not chat_id:
        return jsonify({"error": "Chat ID is required"}), 400
    
    success = delete_chat(g.user['id'], chat_id)
    if success:
        return jsonify({"message": "Chat deleted successfully"}), 200
    return jsonify({"error": "Failed to delete chat or chat not found"}), 400

@app.route('/api/user_profile', methods=['GET'], endpoint='get_user_profile_api') # Explicit endpoint
@login_required
def get_user_profile():
    """
    API endpoint to get the logged-in user's profile details.
    """
    user_details = get_user_by_id(g.user['id'])
    if user_details:
        # Do not send hashed password to frontend
        return jsonify({
            "username": user_details['username'],
            "email": user_details['email']
        })
    return jsonify({"error": "User not found"}), 404

@app.route('/api/user_profile/update', methods=['POST'], endpoint='update_profile_api') # Explicit endpoint
@login_required
def update_profile():
    """
    API endpoint to update the logged-in user's profile details.
    """
    data = request.json
    new_username = data.get('username')
    new_email = data.get('email')
    new_password = data.get('password')

    success = update_user_details(
        g.user['id'], 
        username=new_username, 
        email=new_email, 
        password=new_password
    )

    if success:
        # Reload user details into g.user after update if username/email changed
        g.user = get_user_by_id(g.user['id'])
        return jsonify({"message": "Profile updated successfully", "username": g.user['username'], "email": g.user['email']}), 200
    else:
        # Check if error is due to duplicate email/username
        # This requires more detailed error handling from database.py
        # For now, a generic message is fine.
        return jsonify({"error": "Failed to update profile. Email or username might already be in use."}), 400

if __name__ == '__main__':
    app.run(debug=True) # Set debug=False in production
