# -*- coding: utf-8 -*-
"""
下载历史记录存储（SQLite）
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from src.config import get_config


class HistoryStore:
    """SQLite 下载历史存储"""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._lock = Lock()
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE,
                    url TEXT NOT NULL,
                    title TEXT,
                    platform TEXT,
                    format_id TEXT,
                    quality_label TEXT,
                    resolution TEXT,
                    output_format TEXT,
                    format_ext TEXT,
                    filesize_bytes INTEGER,
                    save_path TEXT,
                    started_at REAL,
                    finished_at REAL,
                    status TEXT,
                    error_message TEXT,
                    audio_extracted INTEGER,
                    include_audio INTEGER,
                    has_audio INTEGER,
                    has_video INTEGER
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_status ON download_history(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_platform ON download_history(platform)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_started ON download_history(started_at)"
            )

    @staticmethod
    def _normalize_platform(platform: str) -> str:
        if not platform:
            return ""
        value = platform.strip().lower()
        if "youtube" in value:
            return "youtube"
        if "twitter" in value or "x.com" in value or value == "x":
            return "x"
        if "bilibili" in value or value == "bili" or value == "b":
            return "bilibili"
        return value

    def record_start(self, task) -> None:
        """记录任务开始"""
        if not task or not task.url:
            return

        config = get_config()
        save_path = str(task.output_path) if task.output_path else str(config.download_path)
        platform = self._normalize_platform(getattr(task, "platform", ""))
        history_id = getattr(task, "history_id", None)

        payload = (
            task.task_id,
            task.url,
            task.title,
            platform,
            task.format_id,
            getattr(task, "quality_label", "") or "",
            getattr(task, "resolution", "") or "",
            task.output_format,
            task.format_ext,
            None,
            save_path,
            task.created_at,
            None,
            task.status.value if hasattr(task.status, "value") else str(task.status),
            task.error_message,
            1 if task.audio_path else 0,
            1 if task.include_audio else 0,
            1 if task.has_audio else 0,
            1 if task.has_video else 0,
        )

        with self._lock:
            with self._connect() as conn:
                if history_id is not None:
                    conn.execute(
                        """
                        UPDATE download_history
                        SET task_id = ?, url = ?, title = ?, platform = ?, format_id = ?,
                            quality_label = ?, resolution = ?, output_format = ?, format_ext = ?,
                            save_path = ?, started_at = ?, finished_at = NULL, status = ?,
                            error_message = NULL, audio_extracted = ?, include_audio = ?, has_audio = ?,
                            has_video = ?
                        WHERE id = ?
                        """,
                        (
                            task.task_id,
                            task.url,
                            task.title,
                            platform,
                            task.format_id,
                            getattr(task, "quality_label", "") or "",
                            getattr(task, "resolution", "") or "",
                            task.output_format,
                            task.format_ext,
                            save_path,
                            task.created_at,
                            task.status.value if hasattr(task.status, "value") else str(task.status),
                            1 if task.audio_path else 0,
                            1 if task.include_audio else 0,
                            1 if task.has_audio else 0,
                            1 if task.has_video else 0,
                            history_id,
                        ),
                    )
                    return

                conn.execute(
                    """
                    INSERT OR IGNORE INTO download_history (
                        task_id, url, title, platform, format_id, quality_label, resolution,
                        output_format, format_ext, filesize_bytes, save_path, started_at,
                        finished_at, status, error_message, audio_extracted, include_audio,
                        has_audio, has_video
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload,
                )
                conn.execute(
                    """
                    UPDATE download_history
                    SET title = ?, platform = ?, format_id = ?, quality_label = ?, resolution = ?,
                        output_format = ?, format_ext = ?, save_path = ?, started_at = COALESCE(started_at, ?),
                        status = ?
                    WHERE task_id = ?
                    """,
                    (
                        task.title,
                        platform,
                        task.format_id,
                        getattr(task, "quality_label", "") or "",
                        getattr(task, "resolution", "") or "",
                        task.output_format,
                        task.format_ext,
                        save_path,
                        task.created_at,
                        task.status.value if hasattr(task.status, "value") else str(task.status),
                        task.task_id,
                    ),
                )

    def record_finish(self, task) -> None:
        """记录任务结束"""
        if not task or not task.url:
            return

        config = get_config()
        save_path = str(task.output_path) if task.output_path else str(config.download_path)
        platform = self._normalize_platform(getattr(task, "platform", ""))
        history_id = getattr(task, "history_id", None)

        filesize_bytes = None
        if getattr(task, "progress", None) and task.progress.total_bytes:
            filesize_bytes = int(task.progress.total_bytes)
        elif task.output_path and Path(task.output_path).exists():
            try:
                filesize_bytes = Path(task.output_path).stat().st_size
            except OSError:
                filesize_bytes = None

        finished_at = task.completed_at if task.completed_at else time.time()
        status_value = task.status.value if hasattr(task.status, "value") else str(task.status)

        with self._lock:
            with self._connect() as conn:
                if history_id is not None:
                    conn.execute(
                        """
                        UPDATE download_history
                        SET title = ?, platform = ?, format_id = ?, quality_label = ?, resolution = ?,
                            output_format = ?, format_ext = ?, filesize_bytes = ?, save_path = ?,
                            finished_at = ?, status = ?, error_message = ?, audio_extracted = ?,
                            include_audio = ?, has_audio = ?, has_video = ?
                        WHERE id = ?
                        """,
                        (
                            task.title,
                            platform,
                            task.format_id,
                            getattr(task, "quality_label", "") or "",
                            getattr(task, "resolution", "") or "",
                            task.output_format,
                            task.format_ext,
                            filesize_bytes,
                            save_path,
                            finished_at,
                            status_value,
                            task.error_message,
                            1 if task.audio_path else 0,
                            1 if task.include_audio else 0,
                            1 if task.has_audio else 0,
                            1 if task.has_video else 0,
                            history_id,
                        ),
                    )
                    return

                cursor = conn.execute(
                    """
                    UPDATE download_history
                    SET title = ?, platform = ?, format_id = ?, quality_label = ?, resolution = ?,
                        output_format = ?, format_ext = ?, filesize_bytes = ?, save_path = ?,
                        finished_at = ?, status = ?, error_message = ?, audio_extracted = ?,
                        include_audio = ?, has_audio = ?, has_video = ?
                    WHERE task_id = ?
                    """,
                    (
                        task.title,
                        platform,
                        task.format_id,
                        getattr(task, "quality_label", "") or "",
                        getattr(task, "resolution", "") or "",
                        task.output_format,
                        task.format_ext,
                        filesize_bytes,
                        save_path,
                        finished_at,
                        status_value,
                        task.error_message,
                        1 if task.audio_path else 0,
                        1 if task.include_audio else 0,
                        1 if task.has_audio else 0,
                        1 if task.has_video else 0,
                        task.task_id,
                    ),
                )
                if cursor.rowcount == 0:
                    conn.execute(
                        """
                        INSERT INTO download_history (
                            task_id, url, title, platform, format_id, quality_label, resolution,
                            output_format, format_ext, filesize_bytes, save_path, started_at,
                            finished_at, status, error_message, audio_extracted, include_audio,
                            has_audio, has_video
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            task.task_id,
                            task.url,
                            task.title,
                            platform,
                            task.format_id,
                            getattr(task, "quality_label", "") or "",
                            getattr(task, "resolution", "") or "",
                            task.output_format,
                            task.format_ext,
                            filesize_bytes,
                            save_path,
                            task.created_at,
                            finished_at,
                            status_value,
                            task.error_message,
                            1 if task.audio_path else 0,
                            1 if task.include_audio else 0,
                            1 if task.has_audio else 0,
                            1 if task.has_video else 0,
                        ),
                    )

    def get_history(
        self,
        status: str = "all",
        platform: str = "all",
        keyword: str = "",
        sort: str = "newest",
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """读取历史记录"""
        status = status or "all"
        platform = platform or "all"
        keyword = (keyword or "").strip()
        sort = sort or "newest"

        clauses = []
        params: List[Any] = []

        if status != "all":
            clauses.append("status = ?")
            params.append(status)
        if platform != "all":
            clauses.append("platform = ?")
            params.append(self._normalize_platform(platform))
        if keyword:
            clauses.append("(title LIKE ? OR url LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        order_clause = (
            "ORDER BY COALESCE(finished_at, started_at) DESC"
            if sort == "newest"
            else "ORDER BY COALESCE(finished_at, started_at) ASC"
        )
        limit_clause = "LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    f"""
                    SELECT *
                    FROM download_history
                    {where_clause}
                    {order_clause}
                    {limit_clause}
                    """,
                    params,
                ).fetchall()

        return [dict(row) for row in rows]

    def delete_history(self, record_id: int) -> bool:
        """删除单条记录"""
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    "DELETE FROM download_history WHERE id = ?",
                    (record_id,),
                )
                return cursor.rowcount > 0

    def clear_history(self) -> int:
        """清空全部历史记录"""
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute("DELETE FROM download_history")
                return cursor.rowcount


_history_instance: Optional[HistoryStore] = None


def get_history_store() -> HistoryStore:
    """获取全局历史记录实例"""
    global _history_instance
    if _history_instance is None:
        config = get_config()
        _history_instance = HistoryStore(config.history_path)
    return _history_instance
