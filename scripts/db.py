"""L3 冷记忆：SQLite 单一事实来源。"""
import sqlite3, time, os

def init_db(path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE IF NOT EXISTS memories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        content TEXT,
        memory_type TEXT,
        source TEXT,
        importance REAL DEFAULT 0.5,
        last_accessed REAL,
        created_at REAL,
        mid_ref TEXT
    )""")
    con.commit()
    return con

def insert(con, user_id, content, memory_type, source, importance=0.5):
    now = time.time()
    cur = con.execute(
        "INSERT INTO memories(user_id,content,memory_type,source,importance,last_accessed,created_at) VALUES(?,?,?,?,?,?,?)",
        (user_id, content, memory_type, source, importance, now, now))
    con.commit()
    return cur.lastrowid

def get_by_id(con, mid):
    return con.execute(
        "SELECT id,user_id,content,memory_type,source,importance,last_accessed,created_at FROM memories WHERE id=?",
        (mid,)).fetchone()

def update_access(con, mid):
    con.execute("UPDATE memories SET last_accessed=? WHERE id=?", (time.time(), mid))
    con.commit()

def list_all(con):
    return con.execute(
        "SELECT id,content,memory_type,source,importance,created_at FROM memories").fetchall()

def count(con):
    return con.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

def clear(con):
    """清空记忆表（用于 consolidation 重新灌入，避免重复累积）。"""
    con.execute("DELETE FROM memories")
    con.commit()
