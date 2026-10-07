import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from business_outreach.models.lead import BusinessLead, LeadStatus, OutreachStatus, WebsiteStatus


class LeadDatabase:

    def __init__(self, database_path: str = "database/business_outreach.db"):
        self.database_path = str(Path(database_path))
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self):
        with self._connection() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, category TEXT DEFAULT '', subcategory TEXT DEFAULT '', business_id TEXT,
                    address TEXT DEFAULT '', city TEXT DEFAULT '', state TEXT DEFAULT '', country TEXT DEFAULT 'India', postal_code TEXT DEFAULT '',
                    latitude REAL, longitude REAL, phone TEXT DEFAULT '', normalized_phone TEXT DEFAULT '', whatsapp_number TEXT DEFAULT '',
                    profile_url TEXT DEFAULT '', maps_url TEXT DEFAULT '', social_url TEXT DEFAULT '',
                    website_url TEXT DEFAULT '', website_status TEXT NOT NULL DEFAULT 'unknown', website_checked_at TEXT,
                    rating REAL, review_count INTEGER, qualified INTEGER NOT NULL DEFAULT 0,
                    qualification_reason TEXT DEFAULT '', qualification_confidence REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'new', source TEXT NOT NULL DEFAULT 'google_business_profile',
                    sample_type TEXT NOT NULL DEFAULT 'none', sample_name TEXT DEFAULT '', sample_url TEXT DEFAULT '',
                    pitch_template TEXT DEFAULT '', pitch_message TEXT DEFAULT '',
                    outreach_status TEXT NOT NULL DEFAULT 'not_started', approval_required INTEGER NOT NULL DEFAULT 1,
                    approved INTEGER NOT NULL DEFAULT 0, approved_at TEXT, contacted_at TEXT, replied_at TEXT, response TEXT DEFAULT '',
                    duplicate_of INTEGER, last_checked_at TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (duplicate_of) REFERENCES leads(id)
                );
                CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(normalized_phone);
                CREATE INDEX IF NOT EXISTS idx_leads_business_id ON leads(business_id);
                CREATE INDEX IF NOT EXISTS idx_leads_profile_url ON leads(profile_url);
                CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
                CREATE INDEX IF NOT EXISTS idx_leads_website_status ON leads(website_status);
                CREATE INDEX IF NOT EXISTS idx_leads_outreach_status ON leads(outreach_status);
            """)

    @staticmethod
    def normalize_phone(phone: str) -> str:
        if not phone:
            return ""
        digits = "".join(c for c in str(phone) if c.isdigit())
        return digits[2:] if digits.startswith("00") and len(digits) > 2 else digits

    @staticmethod
    def normalize_text(value: str) -> str:
        return " ".join(str(value or "").lower().strip().split())

    @staticmethod
    def _enum(value):
        return value.value if hasattr(value, "value") else str(value)

    @staticmethod
    def _dt(value):
        if value is None:
            return None
        return value.isoformat() if isinstance(value, datetime) else str(value)

    def _values(self, lead: BusinessLead):
        return (
            lead.name, lead.category, lead.subcategory, lead.business_id, lead.address, lead.city, lead.state, lead.country, lead.postal_code,
            lead.latitude, lead.longitude, lead.phone, lead.normalized_phone or self.normalize_phone(lead.phone), lead.whatsapp_number,
            lead.profile_url, lead.maps_url, lead.social_url, lead.website_url, self._enum(lead.website_status), self._dt(lead.website_checked_at),
            lead.rating, lead.review_count, int(lead.qualified), lead.qualification_reason, lead.qualification_confidence, self._enum(lead.status),
            self._enum(lead.source), self._enum(lead.sample_type), lead.sample_name, lead.sample_url, lead.pitch_template, lead.pitch_message,
            self._enum(lead.outreach_status), int(lead.approval_required), int(lead.approved), self._dt(lead.approved_at), self._dt(lead.contacted_at),
            self._dt(lead.replied_at), lead.response, lead.duplicate_of, self._dt(lead.last_checked_at), self._dt(lead.created_at),
            self._dt(lead.updated_at), json.dumps(lead.metadata or {}, ensure_ascii=False),
        )

    def add(self, lead: BusinessLead) -> int:
        columns = [
            "name","category","subcategory","business_id","address","city","state","country","postal_code","latitude","longitude",
            "phone","normalized_phone","whatsapp_number","profile_url","maps_url","social_url","website_url","website_status",
            "website_checked_at","rating","review_count","qualified","qualification_reason","qualification_confidence","status","source",
            "sample_type","sample_name","sample_url","pitch_template","pitch_message","outreach_status","approval_required","approved",
            "approved_at","contacted_at","replied_at","response","duplicate_of","last_checked_at","created_at","updated_at","metadata"
        ]
        placeholders = ", ".join("?" for _ in columns)
        with self._connection() as connection:
            cursor = connection.execute(f"INSERT INTO leads ({', '.join(columns)}) VALUES ({placeholders})", self._values(lead))
            return int(cursor.lastrowid)

    def update(self, lead_id: int, lead: BusinessLead) -> bool:
        columns = [
            "name","category","subcategory","business_id","address","city","state","country","postal_code","latitude","longitude",
            "phone","normalized_phone","whatsapp_number","profile_url","maps_url","social_url","website_url","website_status",
            "website_checked_at","rating","review_count","qualified","qualification_reason","qualification_confidence","status","source",
            "sample_type","sample_name","sample_url","pitch_template","pitch_message","outreach_status","approval_required","approved",
            "approved_at","contacted_at","replied_at","response","duplicate_of","last_checked_at","created_at","updated_at","metadata"
        ]
        assignments = ", ".join(f"{c} = ?" for c in columns)
        with self._connection() as connection:
            cursor = connection.execute(f"UPDATE leads SET {assignments} WHERE id = ?", (*self._values(lead), lead_id))
        return cursor.rowcount > 0

    def get(self, lead_id: int) -> Optional[dict]:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None

    def find_existing(self, lead: BusinessLead) -> Optional[dict]:
        phone = lead.normalized_phone or self.normalize_phone(lead.phone)
        with self._connection() as connection:
            checks = []
            if lead.business_id:
                checks.append(("business_id", lead.business_id))
            if lead.profile_url:
                checks.append(("profile_url", lead.profile_url))
            if phone:
                checks.append(("normalized_phone", phone))
            for column, value in checks:
                row = connection.execute(f"SELECT * FROM leads WHERE {column} = ? LIMIT 1", (value,)).fetchone()
                if row:
                    return dict(row)
            name = self.normalize_text(lead.name)
            address = self.normalize_text(lead.address)
            if name and address:
                rows = connection.execute("SELECT * FROM leads WHERE LOWER(TRIM(name)) = ?", (name,)).fetchall()
                for row in rows:
                    if self.normalize_text(row["address"]) == address:
                        return dict(row)
        return None

    def upsert(self, lead: BusinessLead) -> tuple[int, bool]:
        existing = self.find_existing(lead)
        if existing:
            lead_id = int(existing["id"])
            self.update(lead_id, lead)
            return lead_id, False
        return self.add(lead), True

    def list(self, status: Optional[LeadStatus] = None, limit: int = 100) -> list[dict]:
        limit = max(1, min(int(limit), 1000))
        with self._connection() as connection:
            if status is None:
                rows = connection.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            else:
                rows = connection.execute("SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC LIMIT ?", (self._enum(status), limit)).fetchall()
        return [dict(row) for row in rows]

    def list_qualified(self, limit: int = 100) -> list[dict]:
        limit = max(1, min(int(limit), 1000))
        with self._connection() as connection:
            rows = connection.execute("""
                SELECT * FROM leads
                WHERE qualified = 1 AND website_status = ? AND status NOT IN (?, ?)
                ORDER BY created_at DESC LIMIT ?
            """, (WebsiteStatus.NO_WEBSITE_LISTED.value, LeadStatus.DUPLICATE.value, LeadStatus.REJECTED.value, limit)).fetchall()
        return [dict(row) for row in rows]

    def mark_duplicate(self, lead_id: int, original_lead_id: int) -> bool:
        with self._connection() as connection:
            cursor = connection.execute("""
                UPDATE leads SET duplicate_of = ?, status = ?, qualified = 0, updated_at = ? WHERE id = ?
            """, (original_lead_id, LeadStatus.DUPLICATE.value, datetime.now().isoformat(), lead_id))
        return cursor.rowcount > 0

    def count(self, status: Optional[LeadStatus] = None) -> int:
        with self._connection() as connection:
            if status is None:
                row = connection.execute("SELECT COUNT(*) AS count FROM leads").fetchone()
            else:
                row = connection.execute("SELECT COUNT(*) AS count FROM leads WHERE status = ?", (self._enum(status),)).fetchone()
        return int(row["count"])

    def clear_all(self):
        with self._connection() as connection:
            connection.execute("DELETE FROM leads")