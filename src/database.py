import sqlite3
import os
import json
from datetime import datetime

class LocalDatabase:
    """
    Manages local SQLite storage for chats, projects, and context files.
    Ensures complete data privacy on the user's machine.
    """
    def __init__(self, db_path="glm_flash_workspace.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Creates tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    attachments TEXT, -- JSON array of file metadata/images
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def create_project(self, name: str) -> int:
        """Create a new local project library category."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid

    def get_projects(self):
        """Fetch all projects."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at FROM projects ORDER BY id DESC")
            return cursor.fetchall()

    def create_session(self, project_id: int, title: str) -> int:
        """Create a new chat session inside a project."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (project_id, title) VALUES (?, ?)", 
                (project_id, title)
            )
            conn.commit()
            return cursor.lastrowid

    def get_sessions(self, project_id: int):
        """Get all chat sessions for a specific project."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, created_at FROM sessions WHERE project_id = ? ORDER BY id DESC", 
                (project_id,)
            )
            return cursor.fetchall()

    def add_message(self, session_id: int, role: str, content: str, attachments=None):
        """Save a user or assistant message to the database."""
        att_json = json.dumps(attachments) if attachments else "[]"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, attachments) VALUES (?, ?, ?, ?)",
                (session_id, role, content, att_json)
            )
            conn.commit()

    def get_messages(self, session_id: int):
        """Fetch full conversation history for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, attachments, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            return cursor.fetchall()
