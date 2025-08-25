# lib/review.py
from __init__ import CURSOR, CONN


class Review:
    """
    ORM model for annual performance reviews.

    Table: reviews(id INTEGER PRIMARY KEY, year INTEGER, summary TEXT, employee_id INTEGER)
    Relationship: many reviews -> one employee (employees.id)
    """

    # Dictionary of objects saved to the database, keyed by PK id
    all = {}

    def __init__(self, year, summary, employee_id, id=None):
        self._id = None
        self._year = None
        self._summary = None
        self._employee_id = None

        self.id = id
        self.year = year
        self.summary = summary
        self.employee_id = employee_id

    def __repr__(self):
        return (
            f"<Review {self.id}: {self.year}, {self.summary}, "
            f"Employee: {self.employee_id}>"
        )

    # -------------------------
    # Table helpers
    # -------------------------
    @classmethod
    def create_table(cls):
        """Create the reviews table."""
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                summary TEXT,
                employee_id INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        """Drop the reviews table and clear cache."""
        sql = "DROP TABLE IF EXISTS reviews"
        CURSOR.execute(sql)
        CONN.commit()
        cls.all.clear()

    # -------------------------
    # Properties & validation
    # -------------------------
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if value is not None and not isinstance(value, int):
            raise ValueError("id must be an integer or None")
        self._id = value

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        if not isinstance(value, int):
            raise ValueError("year must be an integer")
        if value < 2000:
            raise ValueError("year must be >= 2000")
        self._year = value

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("summary must be a non-empty string")
        self._summary = value

    @property
    def employee_id(self):
        return self._employee_id

    @employee_id.setter
    def employee_id(self, value):
        if not isinstance(value, int):
            raise ValueError("employee_id must be an integer")
        # ensure referenced employee exists in DB (avoid importing Employee here)
        CURSOR.execute("SELECT id FROM employees WHERE id = ?", (value,))
        if CURSOR.fetchone() is None:
            raise ValueError("employee_id must reference a persisted Employee")
        self._employee_id = value

    # -------------------------
    # ORM methods
    # -------------------------
    def save(self):
        """
        Insert a new row with (year, summary, employee_id).
        Set self.id to the new PK and cache this instance.
        """
        if self.id is not None:
            # already persisted; save() in this lab is for inserts only
            return self

        sql = "INSERT INTO reviews (year, summary, employee_id) VALUES (?, ?, ?)"
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id))
        CONN.commit()
        self.id = CURSOR.lastrowid
        type(self).all[self.id] = self
        return self

    @classmethod
    def create(cls, year, summary, employee_id):
        """Build + save a new Review, return the instance."""
        return cls(year, summary, employee_id).save()

    @classmethod
    def instance_from_db(cls, row):
        """
        Given a row (id, year, summary, employee_id), return the cached Review.
        If not cached, create it, cache it, and return it.
        If cached, refresh its attributes from the row.
        """
        rid, year, summary, employee_id = row
        review = cls.all.get(rid)
        if review:
            # refresh attributes directly to avoid re-validating
            review._year = year
            review._summary = summary
            review._employee_id = employee_id
            return review
        review = cls(year, summary, employee_id, id=rid)
        cls.all[rid] = review
        return review

    @classmethod
    def find_by_id(cls, id):
        """Return Review instance by primary key, or None."""
        CURSOR.execute(
            "SELECT id, year, summary, employee_id FROM reviews WHERE id = ?",
            (id,),
        )
        row = CURSOR.fetchone()
        return cls.instance_from_db(row) if row else None

    def update(self):
        """Update the DB row to match current in-memory object."""
        if self.id is None:
            raise ValueError("cannot update a Review without an id")
        sql = """
            UPDATE reviews
            SET year = ?, summary = ?, employee_id = ?
            WHERE id = ?
        """
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id, self.id))
        CONN.commit()
        type(self).all[self.id] = self

    def delete(self):
        """Delete DB row, remove from cache, set id to None."""
        if self.id is None:
            return
        CURSOR.execute("DELETE FROM reviews WHERE id = ?", (self.id,))
        CONN.commit()
        type(self).all.pop(self.id, None)
        self.id = None

    @classmethod
    def get_all(cls):
        """Return a list of Review instances for every row in the table."""
        CURSOR.execute("SELECT id, year, summary, employee_id FROM reviews")
        rows = CURSOR.fetchall()
        return [cls.instance_from_db(row) for row in rows]
