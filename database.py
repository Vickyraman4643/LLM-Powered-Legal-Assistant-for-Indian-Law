# database.py

import sqlite3
import bcrypt
import json
import os
from datetime import datetime
from config import Config

def get_db_connection(db_path):
    """
    Establishes a connection to the specified SQLite database.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error for {db_path}: {e}")
        return None

def init_db():
    """
    Initializes both User_details.db and Chat_history.db,
    creating tables if they don't exist.
    """
    # Initialize User_details.db
    user_conn = get_db_connection(Config.USER_DB_PATH)
    if user_conn:
        try:
            cursor = user_conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
            ''')
            user_conn.commit()
            print("User_details.db initialized successfully.")
        except sqlite3.Error as e:
            print(f"Error initializing User_details.db: {e}")
        finally:
            user_conn.close()

    # Initialize Chat_history.db
    chat_conn = get_db_connection(Config.CHAT_DB_PATH)
    if chat_conn:
        try:
            cursor = chat_conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id TEXT NOT NULL, -- Unique identifier for a chat session
                    title TEXT NOT NULL,
                    messages TEXT NOT NULL, -- Stored as JSON string
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            chat_conn.commit()
            print("Chat_history.db initialized successfully.")
        except sqlite3.Error as e:
            print(f"Error initializing Chat_history.db: {e}")
        finally:
            chat_conn.close()

def add_user(username, email, password):
    """
    Adds a new user to the database after hashing their password.
    Returns the new user's ID on success, None on failure (e.g., email/username taken).
    """
    conn = get_db_connection(Config.USER_DB_PATH)
    if not conn:
        return None

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                       (username, email, hashed_password))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # This error occurs if username or email is not unique
        return None
    except sqlite3.Error as e:
        print(f"Error adding user: {e}")
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    """
    Retrieves a user by their email.
    Returns user dictionary (id, username, email, password) or None if not found.
    """
    conn = get_db_connection(Config.USER_DB_PATH)
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        return dict(user) if user else None
    except sqlite3.Error as e:
        print(f"Error getting user by email: {e}")
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    """
    Retrieves a user by their ID.
    Returns user dictionary (id, username, email, password) or None if not found.
    """
    conn = get_db_connection(Config.USER_DB_PATH)
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    except sqlite3.Error as e:
        print(f"Error getting user by ID: {e}")
        return None
    finally:
        conn.close()

def verify_password(stored_password_hash, provided_password):
    """
    Verifies a provided password against a stored hashed password.
    """
    try:
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password_hash.encode('utf-8'))
    except ValueError:
        # Handles cases where hash might be invalid or not properly encoded
        return False

def update_user_details(user_id, username=None, email=None, password=None):
    """
    Updates user details (username, email, or password).
    Returns True on success, False on failure.
    """
    conn = get_db_connection(Config.USER_DB_PATH)
    if not conn:
        return False
    
    update_fields = []
    update_values = []

    if username:
        update_fields.append("username = ?")
        update_values.append(username)
    if email:
        update_fields.append("email = ?")
        update_values.append(email)
    if password:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_fields.append("password = ?")
        update_values.append(hashed_password)
    
    if not update_fields: # Nothing to update
        conn.close()
        return True

    update_values.append(user_id) # Add user_id for the WHERE clause

    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, tuple(update_values))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # This error occurs if new username or email is not unique
        return False
    except sqlite3.Error as e:
        print(f"Error updating user details: {e}")
        return False
    finally:
        conn.close()

def save_chat_history(user_id, chat_id, title, messages):
    """
    Saves a new chat history or updates an existing one for a user.
    `messages` should be a list of dictionaries, which will be stored as a JSON string.
    """
    conn = get_db_connection(Config.CHAT_DB_PATH)
    if not conn:
        return False
    
    messages_json = json.dumps(messages)
    timestamp = datetime.now().isoformat()

    try:
        cursor = conn.cursor()
        # Check if chat_id already exists for this user_id
        cursor.execute("SELECT id FROM chat_history WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        existing_chat = cursor.fetchone()

        if existing_chat:
            # Update existing chat
            cursor.execute("UPDATE chat_history SET title = ?, messages = ?, timestamp = ? WHERE id = ?",
                           (title, messages_json, timestamp, existing_chat['id']))
        else:
            # Insert new chat
            cursor.execute("INSERT INTO chat_history (user_id, chat_id, title, messages, timestamp) VALUES (?, ?, ?, ?, ?)",
                           (user_id, chat_id, title, messages_json, timestamp))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error saving chat history: {e}")
        return False
    finally:
        conn.close()

def get_chat_history(user_id, chat_id=None):
    """
    Retrieves chat history for a specific user.
    If chat_id is provided, returns that specific chat.
    Otherwise, returns all chat summaries (id, chat_id, title, timestamp) for the user.
    """
    conn = get_db_connection(Config.CHAT_DB_PATH)
    if not conn:
        return [] if chat_id is None else None

    try:
        cursor = conn.cursor()
        if chat_id:
            cursor.execute("SELECT * FROM chat_history WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            chat = cursor.fetchone()
            if chat:
                # Parse messages back to a list of dicts
                chat_dict = dict(chat)
                chat_dict['messages'] = json.loads(chat_dict['messages'])
                return chat_dict
            return None
        else:
            cursor.execute("SELECT id, chat_id, title, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
            chats = cursor.fetchall()
            return [dict(c) for c in chats]
    except sqlite3.Error as e:
        print(f"Error retrieving chat history: {e}")
        return [] if chat_id is None else None
    finally:
        conn.close()

def update_chat_title(user_id, chat_id, new_title):
    """
    Updates the title of a specific chat session for a user.
    """
    conn = get_db_connection(Config.CHAT_DB_PATH)
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE chat_history SET title = ? WHERE user_id = ? AND chat_id = ?",
                       (new_title, user_id, chat_id))
        conn.commit()
        return cursor.rowcount > 0 # Returns true if a row was updated
    except sqlite3.Error as e:
        print(f"Error updating chat title: {e}")
        return False
    finally:
        conn.close()

def delete_chat(user_id, chat_id):
    """
    Deletes a specific chat session for a user.
    """
    conn = get_db_connection(Config.CHAT_DB_PATH)
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE user_id = ? AND chat_id = ?",
                       (user_id, chat_id))
        conn.commit()
        return cursor.rowcount > 0 # Returns true if a row was deleted
    except sqlite3.Error as e:
        print(f"Error deleting chat: {e}")
        return False
    finally:
        conn.close()

# Ensure databases are initialized when this module is imported
# This will create the database folder and files if they don't exist
init_db()
