"""
Excel 单元格底色 → 指标数据来源代码映射。

与录入模板「颜色标示区」一致：
  无颜色 → 地市统计年鉴
  紫色   → 地市年鉴
  浅绿   → 地市级发展公报
  蓝色   → 地市级政府工作报告
  浅蓝   → 省级统计年鉴
  桃红   → 省级年鉴
  黄色   → 专业年鉴
  粉色   → 专项报告
  褐色   → 政府信息公开报告
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from apps.coredata.indicator_sources import IndicatorDataSource

# (名称, RGB, 来源代码) — RGB 取 Excel/WPS 常用标准色
COLOR_SOURCE_RULES: List[Tuple[str, Tuple[int, int, int], str]] = [
    ("purple", (112, 48, 160), IndicatorDataSource.CITY_YB),           # 紫色
    ("light_green", (146, 208, 80), IndicatorDataSource.CITY_DEV_BUL), # 浅绿
    ("light_green_alt", (198, 224, 180), IndicatorDataSource.CITY_DEV_BUL),
    ("blue", (0, 112, 192), IndicatorDataSource.CITY_GOV_RPT),         # 蓝色
    ("blue_alt", (68, 114, 196), IndicatorDataSource.CITY_GOV_RPT),
    ("light_blue", (91, 155, 213), IndicatorDataSource.PROV_STAT_YB),  # 浅蓝
    ("light_blue_alt", (0, 176, 240), IndicatorDataSource.PROV_STAT_YB),
    ("magenta", (255, 102, 153), IndicatorDataSource.PROV_YB),         # 桃红
    ("magenta_alt", (255, 0, 255), IndicatorDataSource.PROV_YB),
    ("yellow", (255, 255, 0), IndicatorDataSource.PROF_YB),            # 黄色
    ("yellow_alt", (255, 192, 0), IndicatorDataSource.PROF_YB),
    ("pink", (255, 199, 206), IndicatorDataSource.SPECIAL_RPT),        # 粉色
    ("pink_alt", (248, 203, 173), IndicatorDataSource.SPECIAL_RPT),
    ("brown", (237, 125, 49), IndicatorDataSource.GOV_INFO_RPT),       # 褐色
    ("brown_alt", (198, 89, 17), IndicatorDataSource.GOV_INFO_RPT),
]

DEFAULT_EXCEL_SOURCE = IndicatorDataSource.CITY_STAT_YB  # 无颜色 / 白色

# 颜色匹配最大欧氏距离（0-441），适当放宽以兼容 WPS 与 Excel 色差
MAX_COLOR_DISTANCE = 95


def _parse_rgb_string(raw: str) -> Optional[Tuple[int, int, int]]:
    if not raw:
        return None
    text = raw.strip().upper()
    if text in ("00000000", "FFFFFFFF", "FFFFFF", "00FFFFFF"):
        if text.endswith("FFFFFF") or text == "FFFFFFFF":
            return (255, 255, 255)
    if len(text) == 8:
        text = text[2:]
    if len(text) != 6:
        return None
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError:
        return None


# openpyxl 标准索引色（常用部分）
_INDEXED_RGB = {
    0: (0, 0, 0),
    1: (255, 255, 255),
    2: (255, 0, 0),
    3: (0, 255, 0),
    4: (0, 0, 255),
    5: (255, 255, 0),
    6: (255, 0, 255),
    7: (0, 255, 255),
    8: (0, 0, 0),
    9: (255, 255, 255),
    10: (255, 0, 0),
    11: (0, 255, 0),
    12: (0, 0, 255),
    13: (255, 255, 0),
    14: (255, 0, 255),
    15: (0, 255, 255),
    22: (198, 89, 17),
    26: (255, 192, 0),
    45: (112, 48, 160),
    46: (146, 208, 80),
    47: (0, 176, 240),
    48: (255, 102, 153),
    49: (0, 112, 192),
}


def get_cell_rgb(cell) -> Optional[Tuple[int, int, int]]:
    """从 openpyxl 单元格读取前景填充 RGB。"""
    fill = cell.fill
    if not fill or fill.fill_type not in (None, "solid"):
        return None

    color = fill.fgColor
    if color is None or color.type == "auto":
        return None

    if color.type == "rgb" and color.rgb:
        return _parse_rgb_string(str(color.rgb))

    if color.type == "indexed" and color.indexed is not None:
        return _INDEXED_RGB.get(int(color.indexed))

    return None


def _color_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def resolve_source_from_rgb(rgb: Optional[Tuple[int, int, int]]) -> str:
    """根据 RGB 匹配最接近的来源代码；无颜色/白色 → 地市统计年鉴。"""
    if rgb is None:
        return DEFAULT_EXCEL_SOURCE

    if _color_distance(rgb, (255, 255, 255)) <= 30:
        return DEFAULT_EXCEL_SOURCE

    best_source = DEFAULT_EXCEL_SOURCE
    best_dist = float("inf")
    for _, rule_rgb, source_code in COLOR_SOURCE_RULES:
        dist = _color_distance(rgb, rule_rgb)
        if dist < best_dist:
            best_dist = dist
            best_source = source_code

    if best_dist <= MAX_COLOR_DISTANCE:
        return best_source
    return DEFAULT_EXCEL_SOURCE


def get_cell_comment_text(cell) -> str:
    if cell.comment and cell.comment.text:
        return str(cell.comment.text).strip()
    return ""


def resolve_source_from_cell(cell) -> str:
    return resolve_source_from_rgb(get_cell_rgb(cell))


def build_cell_payload(cell) -> dict:
    """提取单元格值、来源与备注（批注）。"""
    value = cell.value
    source = resolve_source_from_cell(cell)
    note = get_cell_comment_text(cell)

    # 专业年鉴 / 专项报告：批注中标注具体名称与层级
    if source not in (IndicatorDataSource.PROF_YB, IndicatorDataSource.SPECIAL_RPT):
        note = ""

    return {"value": value, "source": source, "note": note}
