import sqlite3
from typing import List, Dict

class Memory:
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.initialize_schema()

    def initialize_schema(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                tags TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS functions (
                file_path TEXT,
                name TEXT,
                signature TEXT,
                description TEXT,
                tags TEXT,
                PRIMARY KEY (file_path, name),
                FOREIGN KEY (file_path) REFERENCES files(path) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def has_file_info(self, path: str) -> bool:
        query = "SELECT 1 FROM files WHERE path = ? LIMIT 1"
        self.cursor.execute(query, (path,))
        return self.cursor.fetchone() is not None

    def add_or_update_file(self, path: str, tags: List[str]):
        tags_str = ",".join(tags)
        self.cursor.execute("""
            INSERT INTO files (path, tags)
            VALUES (?, ?)
            ON CONFLICT(path) DO UPDATE SET tags = excluded.tags
        """, (path, tags_str))
        self.conn.commit()

    def add_or_update_function(self, file_path: str, name: str, signature: str, description: str, tags: List[str]):
        tags_str = ",".join(tags)
        self.cursor.execute("""
            INSERT INTO functions (file_path, name, signature, description, tags)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(file_path, name) DO UPDATE SET
                signature = excluded.signature,
                description = excluded.description,
                tags = excluded.tags
        """, (file_path, name, signature, description, tags_str))
        self.conn.commit()

    def query_by_tags(self, tags: List[str]) -> List[Dict]:
        tag_filter = " OR ".join(["tags LIKE ?"] * len(tags))
        values = [f"%{tag}%" for tag in tags]
        self.cursor.execute(f"""
            SELECT path, tags FROM files
            WHERE {tag_filter}
        """, values)
        files = self.cursor.fetchall()

        results = []
        for path, file_tags in files:
            self.cursor.execute("""
                SELECT name, signature, description, tags
                FROM functions
                WHERE file_path = ?
            """, (path,))
            functions = self.cursor.fetchall()
            functions_list = [
                {
                    "name": name,
                    "signature": signature,
                    "description": description,
                    "tags": fn_tags
                }
                for name, signature, description, fn_tags in functions
            ]
            results.append({
                "path": path,
                "tags": file_tags,
                "functions": functions_list
            })

        return results

    def clear(self):
        self.cursor.execute("DELETE FROM functions")
        self.cursor.execute("DELETE FROM files")
        self.conn.commit()

    def get_all_files(self) -> List[Dict]:
        self.cursor.execute("SELECT path, tags FROM files")
        files = self.cursor.fetchall()
        results = []
        for path, file_tags in files:
            self.cursor.execute("""
                SELECT name, signature, description, tags
                FROM functions
                WHERE file_path = ?
            """, (path,))
            functions = self.cursor.fetchall()
            functions_list = [
                {
                    "name": name,
                    "signature": signature,
                    "description": description,
                    "tags": fn_tags
                }
                for name, signature, description, fn_tags in functions
            ]
            results.append({
                "path": path,
                "tags": file_tags,
                "functions": functions_list
            })
        return results


memory = Memory()