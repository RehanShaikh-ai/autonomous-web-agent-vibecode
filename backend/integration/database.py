import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional
from shared.schemas import BrowserResult, GoalSchema, PlanStep

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database failures."""

    pass


class SessionDatabase:
    """Handles thread-safe SQLite persistence for agent task execution runs."""

    def __init__(self, db_path: str = "sessions.db") -> None:
        """Initializes the database connection and creates tables if missing.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Helper to establish a connection with JSON support configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Creates the session tracking tables if they do not exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        goal_id TEXT PRIMARY KEY,
                        objective TEXT NOT NULL,
                        constraints TEXT NOT NULL,
                        status TEXT NOT NULL,
                        confidence_score REAL,
                        final_report TEXT
                    )
                """)
                # Steps table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS steps (
                        goal_id TEXT,
                        step_id INTEGER,
                        action TEXT NOT NULL,
                        url TEXT,
                        selector TEXT,
                        input_value TEXT,
                        description TEXT NOT NULL,
                        PRIMARY KEY (goal_id, step_id),
                        FOREIGN KEY (goal_id) REFERENCES sessions(goal_id) ON DELETE CASCADE
                    )
                """)
                # Browser outcomes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS browser_results (
                        goal_id TEXT,
                        step_id INTEGER,
                        status TEXT NOT NULL,
                        final_url TEXT NOT NULL,
                        raw_html TEXT NOT NULL,
                        screenshot_path TEXT,
                        error_message TEXT,
                        PRIMARY KEY (goal_id, step_id),
                        FOREIGN KEY (goal_id) REFERENCES sessions(goal_id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
            logger.info("Session database initialized successfully at: %s", self.db_path)
        except sqlite3.Error as e:
            logger.error("Failed to initialize database: %s", str(e))
            raise DatabaseError(f"Database init failure: {e}")

    def create_session(self, goal: GoalSchema, steps: List[PlanStep]) -> None:
        """Saves a new goal session along with its planned steps.

        Args:
            goal: The parsed user GoalSchema.
            steps: The list of PlanStep execution items.

        Raises:
            DatabaseError: If database write fails.
        """
        logger.info("Saving new goal session: %s", goal.goal_id)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO sessions (goal_id, objective, constraints, status, confidence_score, final_report)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        goal.goal_id,
                        goal.objective,
                        json.dumps(goal.constraints),
                        "planned",
                        None,
                        None,
                    ),
                )

                for step in steps:
                    cursor.execute(
                        """
                        INSERT INTO steps (goal_id, step_id, action, url, selector, input_value, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            goal.goal_id,
                            step.step_id,
                            step.action.value,
                            step.url,
                            step.selector,
                            step.input_value,
                            step.description,
                        ),
                    )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Failed to write session %s: %s", goal.goal_id, str(e))
            raise DatabaseError(f"Create session failure: {e}")

    def update_session_status(self, goal_id: str, status: str) -> None:
        """Updates the operational status of a session (e.g. running, completed).

        Args:
            goal_id: The ID of the target session.
            status: The new status string.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE sessions SET status = ? WHERE goal_id = ?",
                    (status, goal_id),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Failed to update status for %s: %s", goal_id, str(e))
            raise DatabaseError(f"Update status failure: {e}")

    def save_browser_result(self, goal_id: str, result: BrowserResult) -> None:
        """Persists the outcome of a single browser navigation step.

        Args:
            goal_id: The active session goal ID.
            result: The step outcomes.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO browser_results (goal_id, step_id, status, final_url, raw_html, screenshot_path, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        goal_id,
                        result.step_id,
                        result.status,
                        result.final_url,
                        result.raw_html,
                        result.screenshot_path,
                        result.error_message,
                    ),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Failed to save step result for %s step %d: %s", goal_id, result.step_id, str(e))
            raise DatabaseError(f"Save browser result failure: {e}")

    def save_final_report(self, goal_id: str, report_json: str, confidence: float) -> None:
        """Saves the final verification report and scores.

        Args:
            goal_id: The session goal ID.
            report_json: Serialized JSON report output.
            confidence: Float confidence value.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE sessions
                    SET status = 'completed', confidence_score = ?, final_report = ?
                    WHERE goal_id = ?
                """,
                    (confidence, report_json, goal_id),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Failed to finalize session %s: %s", goal_id, str(e))
            raise DatabaseError(f"Save final report failure: {e}")

    def get_session(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw session metadata, steps, and results.

        Args:
            goal_id: Target session ID.

        Returns:
            A dictionary containing session details, steps, and browser outcomes if found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sessions WHERE goal_id = ?", (goal_id,))
                session_row = cursor.fetchone()
                if not session_row:
                    return None

                session_dict = dict(session_row)
                session_dict["constraints"] = json.loads(session_dict["constraints"])

                cursor.execute("SELECT * FROM steps WHERE goal_id = ? ORDER BY step_id ASC", (goal_id,))
                session_dict["steps"] = [dict(r) for r in cursor.fetchall()]

                cursor.execute("SELECT * FROM browser_results WHERE goal_id = ?", (goal_id,))
                session_dict["results"] = [dict(r) for r in cursor.fetchall()]

                return session_dict
        except sqlite3.Error as e:
            logger.error("Failed to retrieve session %s: %s", goal_id, str(e))
            raise DatabaseError(f"Get session failure: {e}")
