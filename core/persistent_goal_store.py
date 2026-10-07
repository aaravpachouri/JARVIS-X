from __future__ import annotations
import json, sqlite3, time, uuid
from pathlib import Path
from typing import Any, Optional

class PersistentGoalStore:
    """SQLite persistence layer for GoalContext."""
    def __init__(self, db_path: str | Path = "database/jarvis_goals.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        c = sqlite3.connect(str(self.db_path), timeout=10.0)
        c.row_factory = sqlite3.Row
        return c

    def _initialize(self):
        c = self._connect()
        try:
            c.execute("""CREATE TABLE IF NOT EXISTS goals(
                goal_id TEXT PRIMARY KEY, title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'ACTIVE',
                priority INTEGER NOT NULL DEFAULT 50, created_at REAL NOT NULL,
                updated_at REAL NOT NULL, due_at REAL,
                metadata_json TEXT NOT NULL DEFAULT '{}', progress REAL NOT NULL DEFAULT 0.0)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority DESC)")
            c.commit()
        finally:
            c.close()

    def save(self, goal=None, *, goal_data: Optional[dict[str, Any]] = None):
        data = dict(goal_data if goal_data is not None else goal.to_dict())
        gid = str(data.get("goal_id") or uuid.uuid4())
        now = time.time()
        c = self._connect()
        try:
            c.execute("""INSERT INTO goals(
                goal_id,title,description,status,priority,created_at,updated_at,
                due_at,metadata_json,progress)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(goal_id) DO UPDATE SET
                title=excluded.title,description=excluded.description,status=excluded.status,
                priority=excluded.priority,updated_at=excluded.updated_at,due_at=excluded.due_at,
                metadata_json=excluded.metadata_json,progress=excluded.progress""",
                (gid, str(data.get("title","")), str(data.get("description","")),
                 str(data.get("status","ACTIVE")), int(data.get("priority",50) or 50),
                 float(data.get("created_at",now) or now), float(data.get("updated_at",now) or now),
                 data.get("due_at"), json.dumps(data.get("metadata",{}) or {}, default=str),
                 float(data.get("progress",0.0) or 0.0)))
            c.commit()
        finally:
            c.close()
        data["goal_id"] = gid
        return data

    def get(self, goal_id: str):
        c = self._connect()
        try:
            r = c.execute("SELECT * FROM goals WHERE goal_id=?", (str(goal_id),)).fetchone()
            return self._row(r) if r else None
        finally:
            c.close()

    def active(self, limit=20):
        c = self._connect()
        try:
            rows = c.execute("""SELECT * FROM goals WHERE status='ACTIVE'
                ORDER BY priority DESC, updated_at DESC LIMIT ?""", (max(1,int(limit)),)).fetchall()
            return [self._row(r) for r in rows]
        finally:
            c.close()

    def search(self, query: str, limit=20):
        q = str(query or "").strip().lower()
        if not q: return []
        like = f"%{q}%"
        c = self._connect()
        try:
            rows = c.execute("""SELECT * FROM goals
                WHERE LOWER(title) LIKE ? OR LOWER(description) LIKE ?
                ORDER BY priority DESC, updated_at DESC LIMIT ?""",
                (like, like, max(1,int(limit)))).fetchall()
            return [self._row(r) for r in rows]
        finally:
            c.close()

    def delete(self, goal_id: str):
        c = self._connect()
        try:
            cur = c.execute("DELETE FROM goals WHERE goal_id=?", (str(goal_id),))
            c.commit()
            return cur.rowcount > 0
        finally:
            c.close()

    @staticmethod
    def _row(r):
        try: meta = json.loads(r["metadata_json"])
        except Exception: meta = {}
        return {
            "goal_id": r["goal_id"], "title": r["title"], "description": r["description"],
            "status": r["status"], "priority": int(r["priority"]), "created_at": r["created_at"],
            "updated_at": r["updated_at"], "due_at": r["due_at"], "metadata": meta,
            "progress": float(r["progress"])
        }