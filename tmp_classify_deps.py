import json

from apps.coredata.calc_indicators import CALC_INDICATORS
from apps.coredata.indicator_catalog import (
    get_form_indicator_categories,
    get_indicator_catalog_dict,
)
from apps.coredata.management.commands.indicator_zh_en import INDIMAP, INDIMAP_UNIT
from apps.coredata.services.input_form_service import strip_unit_suffix

en_to_zh = {v: k for k, v in INDIMAP.items()}
report = json.load(open("/tmp/calc_coverage_report.json"))
missing_from_db = set()
for row in report["rows"]:
    missing_from_db.update(row.get("missing") or [])

form_zh = {
    strip_unit_suffix(x)
    for xs in get_form_indicator_categories("city").values()
    for x in xs
}
catalog_zh = {x for xs in get_indicator_catalog_dict().values() for x in xs}
auto = {r["name_en"] for r in CALC_INDICATORS if r.get("expr")}
auto_zh = {r["name_zh"] for r in CALC_INDICATORS if r.get("expr")}

rows = []
for en in sorted(missing_from_db):
    zh = en_to_zh.get(en)
    in_map = zh is not None
    in_form = bool(zh and zh in form_zh)
    in_catalog = bool(zh and zh in catalog_zh)
    is_calc = en in auto or (zh in auto_zh if zh else False)
    rows.append(
        dict(
            en=en,
            zh=zh,
            in_map=in_map,
            in_form=in_form,
            in_catalog=in_catalog,
            is_calc=is_calc,
            in_unit=en in INDIMAP_UNIT,
        )
    )

ok_enter = [r for r in rows if r["in_map"] and r["in_form"] and not r["is_calc"]]
ok_map_not_form = [
    r for r in rows if r["in_map"] and not r["in_form"] and not r["is_calc"]
]
no_map = [r for r in rows if not r["in_map"]]
is_calc_dep = [r for r in rows if r["is_calc"]]

print(f"库中缺失依赖字段数: {len(missing_from_db)}\n")
print(f"【是基础指标，可在录入表单填】 {len(ok_enter)}")
for r in ok_enter:
    print(f"  {r['zh']}  ({r['en']})")
print(f"\n【映射有，但不在当前录入表单】 {len(ok_map_not_form)}")
for r in ok_map_not_form:
    print(
        f"  {r['zh']}  ({r['en']})  catalog={r['in_catalog']} unit={r['in_unit']}"
    )
print(f"\n【映射里没有】 {len(no_map)}")
for r in no_map:
    print(f"  {r['en']} unit={r['in_unit']}")
print(f"\n【依赖本身是计算指标】 {len(is_calc_dep)}")
for r in is_calc_dep:
    print(f"  {r['zh']} ({r['en']})")

print("\n=== 缺依赖的计算指标：补录后能否算 ===")
fully = 0
for row in report["rows"]:
    if row["status"] != "缺依赖":
        continue
    miss = row["missing"]
    ok = True
    details = []
    for en in miss:
        zh = en_to_zh.get(en)
        if not zh or zh not in form_zh or en in auto:
            ok = False
            details.append(f"{en}(不可录/非基础)")
        else:
            details.append(zh)
    flag = "可" if ok else "否/部分"
    if ok:
        fully += 1
    print(f"  {flag}: {row['name_zh']} <- {', '.join(details)}")
print(f"\n完全靠补录基础项就能算的缺依赖项: {fully}")
