"""
Excel 指标录入异步任务：请求只落盘并立刻返回，解析/写库/计算在后台线程执行。
"""
from __future__ import annotations

import logging
import os
import tempfile
import threading
import uuid
from pathlib import Path
from typing import BinaryIO, Literal

from apps.coredata.services.excel_upload_service import (
    extract_cell_fields,
    parse_area_indicator_excel,
    parse_city_indicator_excel,
)

logger = logging.getLogger(__name__)

ImportKind = Literal["city", "area"]

_UPLOAD_DIR = Path(tempfile.gettempdir()) / "gov_excel_imports"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_upload_to_disk(uploaded_file: BinaryIO, original_name: str = "") -> str:
    name = original_name or getattr(uploaded_file, "name", "") or "upload.xlsx"
    suffix = Path(name).suffix.lower() or ".xlsx"
    if suffix not in (".xlsx", ".xls"):
        suffix = ".xlsx"
    path = _UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    with open(path, "wb") as out:
        chunks = getattr(uploaded_file, "chunks", None)
        if callable(chunks):
            for chunk in uploaded_file.chunks():
                out.write(chunk)
        else:
            out.write(uploaded_file.read())
    return str(path)


def _normalize_area_rows(rows_data: list) -> list:
    if not rows_data:
        return []

    city_col = next((c for c in rows_data[0] if c in ["城市", "城市名称", "地市"]), None)
    if not city_col:
        city_col = next((c for c in rows_data[0] if "城市" in str(c)), None)

    area_col = next(
        (
            c
            for c in rows_data[0]
            if c
            in [
                "所辖区县名称",
                "所辖区域名称",
                "区县",
                "区县名称",
                "区县名",
                "区域名称",
            ]
        ),
        None,
    )
    if not area_col:
        area_col = next(
            (c for c in rows_data[0] if ("区县" in str(c) or "区域" in str(c))),
            None,
        )

    if not city_col or not area_col:
        raise ValueError('Excel缺少“城市/城市名称”或“所辖区域名称/所辖区县名称/区县”列')

    normalized_rows = []
    last_city = ""
    for row in rows_data:
        city_val, _, _ = extract_cell_fields(row.get(city_col))
        city_name = str(city_val).strip() if city_val is not None else ""
        if city_name:
            last_city = city_name
        else:
            city_name = last_city

        area_val, _, _ = extract_cell_fields(row.get(area_col))
        area_name = str(area_val).strip() if area_val is not None else ""
        if (
            not city_name
            or not area_name
            or city_name in ("nan", "None")
            or area_name in ("nan", "None")
        ):
            continue

        normalized = dict(row)
        normalized["城市"] = city_name
        normalized["area"] = area_name
        normalized_rows.append(normalized)

    if not normalized_rows:
        raise ValueError("Excel 无有效城市/区县数据行")
    return normalized_rows


def _run_city_import(file_path: str, year: int, job_id: str) -> None:
    from apps.dashboard.views import save_df_to_database

    with open(file_path, "rb") as f:
        rows_data = parse_city_indicator_excel(f)
    if not rows_data:
        raise ValueError("Excel 无有效数据行")
    # 已在后台线程，计算同步跑完即可，避免再套一层线程
    save_df_to_database(rows_data=rows_data, year=year, background_calc=False)
    logger.info("excel city import done job=%s year=%s rows=%s", job_id, year, len(rows_data))


def _run_area_import(file_path: str, year: int, job_id: str) -> None:
    from apps.dashboard.views import save_area_df_to_database

    with open(file_path, "rb") as f:
        rows_data = parse_area_indicator_excel(f)
    if not rows_data:
        raise ValueError("Excel 无有效数据行")
    normalized = _normalize_area_rows(rows_data)
    save_area_df_to_database(rows_data=normalized, year=year)
    logger.info(
        "excel area import done job=%s year=%s rows=%s",
        job_id,
        year,
        len(normalized),
    )


def schedule_excel_import(*, kind: ImportKind, file_path: str, year: int) -> str:
    """
    后台导入。返回 job_id。
    """
    job_id = uuid.uuid4().hex[:12]

    def _worker() -> None:
        from django.db import close_old_connections

        close_old_connections()
        try:
            if kind == "city":
                _run_city_import(file_path, year, job_id)
            else:
                _run_area_import(file_path, year, job_id)
        except Exception:
            logger.exception(
                "excel import failed job=%s kind=%s year=%s path=%s",
                job_id,
                kind,
                year,
                file_path,
            )
        finally:
            close_old_connections()
            try:
                os.remove(file_path)
            except OSError:
                pass

    threading.Thread(
        target=_worker,
        name=f"excel-import-{kind}-{job_id}",
        daemon=True,
    ).start()
    logger.info(
        "excel import scheduled job=%s kind=%s year=%s path=%s",
        job_id,
        kind,
        year,
        file_path,
    )
    return job_id
