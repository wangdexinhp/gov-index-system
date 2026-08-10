"""
根据 city_id + year 已有录入指标，计算计算型指标并写回 Indicator。
"""
from __future__ import annotations

import ast
import logging
import operator
import threading
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from apps.coredata.calc_indicators import CALC_INDICATORS, CalcIndicator

logger = logging.getLogger(__name__)

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        try:
            return float(value)
        except (InvalidOperation, ValueError):
            return None
    try:
        text = str(value).strip()
        if not text or text.lower() in ("nan", "none", "null", "-", "—", "a"):
            return None
        return float(text.replace(",", ""))
    except (TypeError, ValueError):
        return None


def _safe_eval(expr: str, variables: Dict[str, float]) -> Optional[float]:
    """仅允许数字字面量与 + - * / ** () 及变量名。"""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return None

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Num):  # py<3.8 compat
            return float(node.n)
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise KeyError(node.id)
            return float(variables[node.id])
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _BIN_OPS:
                raise ValueError(f"unsupported op {op_type}")
            left = _eval(node.left)
            right = _eval(node.right)
            if op_type is ast.Div and right == 0:
                raise ZeroDivisionError
            return float(_BIN_OPS[op_type](left, right))
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _UNARY_OPS:
                raise ValueError(f"unsupported unary {op_type}")
            return float(_UNARY_OPS[op_type](_eval(node.operand)))
        raise ValueError(f"unsupported expression node {type(node)}")

    try:
        result = _eval(tree)
    except (KeyError, ZeroDivisionError, ValueError, TypeError, OverflowError):
        return None
    if result != result:  # NaN
        return None
    return float(result)


def _load_values(city_id: int, year: int, name_ens: Iterable[str]) -> Dict[str, float]:
    from apps.coredata.models.indicator import Indicator

    name_set = set(name_ens)
    if not name_set:
        return {}
    rows = Indicator.objects.filter(
        city_id=city_id,
        year=year,
        name_en__in=name_set,
    ).values_list("name_en", "value")
    out: Dict[str, float] = {}
    for name_en, value in rows:
        num = _to_float(value)
        if num is not None:
            out[name_en] = num
    return out


def _collect_dep_names(rules: Iterable[CalcIndicator]) -> Set[str]:
    names: Set[str] = set()
    for rule in rules:
        names.update(rule.get("deps") or [])
    return names


def compute_computed_indicators_for_city_year(
    city_id: int,
    year: int,
    *,
    province_id: int = 0,
    persist: bool = True,
) -> Dict[str, float]:
    """
    计算某城市某年全部可计算指标。
    返回 {name_en: value}；persist=True 时以 input_form=CALC 写回 Indicator。
    """
    if not city_id or not year:
        return {}

    rules = [r for r in CALC_INDICATORS if r.get("expr")]
    if not rules:
        return {}

    dep_names = _collect_dep_names(rules)
    current_vals = _load_values(city_id, int(year), dep_names)

    need_prev = any(r.get("needs_prev_year") for r in rules)
    prev_vals: Dict[str, float] = {}
    if need_prev:
        prev_vals = _load_values(city_id, int(year) - 1, dep_names)

    variables: Dict[str, float] = dict(current_vals)
    for name, value in prev_vals.items():
        variables[f"prev_{name}"] = value

    results: Dict[str, float] = {}
    for rule in rules:
        expr = rule.get("expr")
        if not expr:
            continue
        # 缺依赖则跳过（含上年依赖）
        missing = False
        for dep in rule.get("deps") or []:
            if dep not in current_vals:
                missing = True
                break
            if rule.get("needs_prev_year") and f"prev_{dep}" not in variables:
                missing = True
                break
        if missing:
            continue

        value = _safe_eval(expr, variables)
        if value is None:
            continue
        # 保留合理精度
        value = round(value, 6)
        results[rule["name_en"]] = value
        variables[rule["name_en"]] = value

    if persist and results:
        _persist_results(
            city_id=int(city_id),
            year=int(year),
            province_id=int(province_id or 0),
            results=results,
        )
    return results


def _persist_results(
    *,
    city_id: int,
    year: int,
    province_id: int,
    results: Dict[str, float],
) -> None:
    from apps.coredata.models.indicator import Indicator

    rule_map = {r["name_en"]: r for r in CALC_INDICATORS}
    for name_en, value in results.items():
        rule = rule_map.get(name_en)
        if not rule:
            continue
        try:
            Indicator.objects.update_or_create(
                year=year,
                city_id=city_id,
                name_en=name_en,
                defaults={
                    "province_id": province_id,
                    "value": value,
                    "name_zh": rule["name_zh"],
                    "source": "系统自动计算",
                    "note": "",
                    "input_method": Indicator.InputMethod.MANUAL,
                    "input_form": Indicator.InputForm.CALC,
                    "indicator_type": Indicator.IndicatorType.OTHER,
                },
            )
        except Exception:
            logger.exception(
                "persist calc indicator failed city=%s year=%s name_en=%s",
                city_id,
                year,
                name_en,
            )


def recompute_for_city_years(city_year_pairs: Iterable[tuple[int, int, int]]) -> int:
    """
    batch: iterable of (city_id, year, province_id)
    返回成功算出的指标条数（跨城市合计）。
    """
    total = 0
    seen = set()
    for city_id, year, province_id in city_year_pairs:
        key = (int(city_id), int(year))
        if key in seen or not city_id or not year:
            continue
        seen.add(key)
        total += len(
            compute_computed_indicators_for_city_year(
                city_id=city_id,
                year=year,
                province_id=province_id or 0,
                persist=True,
            )
        )
    return total


def _dedupe_city_year_pairs(
    city_year_pairs: Iterable[tuple[int, int, int]],
) -> List[Tuple[int, int, int]]:
    seen = set()
    out: List[Tuple[int, int, int]] = []
    for city_id, year, province_id in city_year_pairs:
        if not city_id or not year:
            continue
        key = (int(city_id), int(year))
        if key in seen:
            continue
        seen.add(key)
        out.append((int(city_id), int(year), int(province_id or 0)))
    return out


def schedule_recompute_for_city_years(
    city_year_pairs: Iterable[tuple[int, int, int]],
) -> int:
    """
    后台线程执行自动计算，避免 Excel 大批量录入拖垮 HTTP 请求。
    返回已调度的「城市×年份」数量（0 表示无需调度）。
    """
    pairs = _dedupe_city_year_pairs(city_year_pairs)
    if not pairs:
        return 0

    def _worker(job_pairs: List[Tuple[int, int, int]]) -> None:
        from django.db import close_old_connections

        close_old_connections()
        try:
            n = recompute_for_city_years(job_pairs)
            logger.info(
                "background calc finished cities=%s wrote=%s",
                len(job_pairs),
                n,
            )
        except Exception:
            logger.exception(
                "background calc failed cities=%s",
                len(job_pairs),
            )
        finally:
            close_old_connections()

    threading.Thread(
        target=_worker,
        args=(pairs,),
        name="calc-indicators-recompute",
        daemon=True,
    ).start()
    logger.info("background calc scheduled cities=%s", len(pairs))
    return len(pairs)
