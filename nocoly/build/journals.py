#!/usr/bin/env python3
"""Build the Phase 1 Journals worksheet in ERP Master through hap-cli only.

The worksheet and menu group were created during the approved preflight. This
builder replaces only the three stock controls on an empty Journals worksheet,
then configures its two table views. It never touches Contacts, Products, or
Units & Packagings.

    python nocoly/build/journals.py fields
    python nocoly/build/journals.py views
    python nocoly/build/journals.py verify
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROFILE = "fbmy-nocoly"
APP = "6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9"
WORKSHEET = "6aa8f5191204328eb1af162a"
DEFAULT_VIEW = "6aa8f5191204328eb1af162e"
HERE = Path(__file__).resolve().parent
BACKUPS = HERE / "backups"


def run(*args):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    command = ["hap", "--profile", PROFILE, "--json", *args]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180, env=env)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout) if result.stdout.strip() else None


def default(value):
    return json.dumps([{"cid": "", "rcid": "", "staticValue": str(value)}])


def option(key, value, index, color, checked=False):
    return {
        "key": key,
        "value": value,
        "isDeleted": False,
        "index": index,
        "checked": checked,
        "color": color,
    }


TYPE_OPTIONS = [
    option("1eb997f4-66ba-4ee1-b310-2cc245807aa1", "Sales", 1, "#C9E6FC"),
    option("3649719d-d164-49bc-ac0e-026a83917942", "Purchase", 2, "#C3F2F2"),
    option("97f495e4-79bf-405a-9f01-93e53b3c7f2c", "Cash", 3, "#C2F1D2"),
    option("ab62f2c4-8e86-4028-8f28-c8700eef77e8", "Bank", 4, "#FFE7B1"),
    option("b3fa50b5-9807-456d-ac71-bb2176b545bb", "Credit Card", 5, "#FBD2BF"),
    option("f342c982-c1d1-40c1-8bd8-308e0f77a94a", "Miscellaneous", 6, "#D2D2D2"),
]
COMMUNICATION_TYPE_OPTIONS = [
    option("46c0154b-ad58-4c28-9ff0-896972093807", "Based on Customer", 1, "#C9E6FC"),
    option("3758ebd7-5b28-41ec-964d-9a3747316617", "Based on Invoice", 2, "#C3F2F2", True),
]
COMMUNICATION_STANDARD_OPTIONS = [
    option(
        "09f530e3-f017-46fe-8a4f-2ba6fb5e6cb8",
        "Full Reference (INV/2024/00001)",
        1,
        "#C9E6FC",
        True,
    ),
    option(
        "b7cc8520-1f95-455b-a0b7-1be84a127c27",
        "European (RF83INV202400001)",
        2,
        "#C3F2F2",
    ),
    option(
        "8ca4b321-5330-4f8f-be61-a4012450214b",
        "Numbers only (202400001)",
        3,
        "#C2F1D2",
    ),
]


def controls():
    return [
        {
            "controlId": "51f598c8-f3d8-40ce-96e7-9d1188c9300f",
            "controlName": "Journal Name",
            "alias": "name",
            "type": 2,
            "row": 0,
            "col": 0,
            "size": 12,
            "enumDefault": 2,
            "attribute": 1,
            "required": True,
            "unique": False,
            "fieldPermission": "111",
            "hint": "Enter journal name",
        },
        {
            "controlId": "4fa64511-c2bc-4fdc-897d-b7b55df155fb",
            "controlName": "Sequence Prefix",
            "alias": "code",
            "type": 2,
            "row": 1,
            "col": 0,
            "size": 6,
            "enumDefault": 2,
            "required": True,
            "unique": False,
            "fieldPermission": "111",
            "hint": "Enter up to 5 characters",
            "desc": "A short prefix of up to 5 characters used to identify the journal.",
        },
        {
            "controlId": "c0f4c31c-ce92-43e3-8bba-9acdcb203fa7",
            "controlName": "Type",
            "alias": "type",
            "type": 11,
            "row": 1,
            "col": 1,
            "size": 6,
            "enumDefault2": 0,
            "required": True,
            "unique": False,
            "fieldPermission": "111",
            "hint": "Select a journal type",
            "advancedSetting": {"showtype": "0"},
            "options": TYPE_OPTIONS,
        },
        {
            "controlId": "87bd8905-d968-420f-a602-0b67a1e2dc4e",
            "controlName": "Communication Type",
            "alias": "invoice_reference_type",
            "type": 11,
            "row": 2,
            "col": 0,
            "size": 6,
            "enumDefault2": 0,
            "required": False,
            "unique": False,
            "fieldPermission": "111",
            "hint": "Select a communication type",
            "advancedSetting": {
                "showtype": "0",
                "defsource": default("3758ebd7-5b28-41ec-964d-9a3747316617"),
            },
            "options": COMMUNICATION_TYPE_OPTIONS,
        },
        {
            "controlId": "a06ee75f-3f65-4690-a229-995c8a83c16e",
            "controlName": "Communication Standard",
            "alias": "invoice_reference_model",
            "type": 11,
            "row": 2,
            "col": 1,
            "size": 6,
            "enumDefault2": 0,
            "required": False,
            "unique": False,
            "fieldPermission": "111",
            "hint": "Select a communication standard",
            "advancedSetting": {
                "showtype": "0",
                "defsource": default("09f530e3-f017-46fe-8a4f-2ba6fb5e6cb8"),
            },
            "options": COMMUNICATION_STANDARD_OPTIONS,
        },
        {
            "controlId": "4822d983-8a66-4146-af60-b5c64b938053",
            "controlName": "Active",
            "alias": "active",
            "type": 36,
            "row": 3,
            "col": 0,
            "size": 6,
            "required": False,
            "unique": False,
            "fieldPermission": "011",
            "advancedSetting": {"defsource": default(1), "showtype": "0"},
            "desc": "Uncheck Active to archive a journal without deleting it.",
        },
        {
            "controlId": "6d6228c4-a0af-41d0-b241-e77805158f39",
            "controlName": "Sequence",
            "alias": "sequence",
            "type": 6,
            "row": 3,
            "col": 1,
            "size": 6,
            "dot": 0,
            "required": False,
            "unique": False,
            "fieldPermission": "011",
            "advancedSetting": {"defsource": default(10), "dotformat": "1", "roundtype": "2"},
            "desc": "Technical order used to sort journals.",
        },
    ]


def live_controls():
    return run("worksheet", "fields", WORKSHEET, "--raw")


def records():
    result = run("worksheet", "record", "list", WORKSHEET, "-a", APP, "-n", "1", "-p", "1")
    data = result.get("data", result)
    return data.get("total", len(data.get("rows", [])))


def backup(name, value):
    BACKUPS.mkdir(exist_ok=True)
    path = BACKUPS / f"{name}_{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def step_fields():
    current = live_controls()
    names = {control["controlName"] for control in current}
    expected = {control["controlName"] for control in controls()}
    if records() != 0:
        raise SystemExit("Journals has records; refusing to replace its field layout.")
    if names == expected and len(current) == len(expected):
        print("Journals already has the expected seven controls; no field save performed.")
        step_verify()
        return
    if len(current) > 3:
        raise SystemExit(f"Unexpected existing controls; refusing to replace them: {sorted(names)}")
    print("Backup:", backup("journals_controls_pre_fields", current))
    run("worksheet", "update-fields", WORKSHEET, "--controls", json.dumps(controls(), ensure_ascii=False))
    step_verify()


def step_verify():
    current = live_controls()
    summary = [
        {
            "name": item["controlName"],
            "type": item["type"],
            "alias": item.get("alias"),
            "title": item.get("attribute") == 1,
            "required": item.get("required"),
            "permission": item.get("fieldPermission"),
            "hint": item.get("hint"),
            "default": item.get("advancedSetting", {}).get("defsource"),
            "options": [
                {"value": option["value"], "default": option.get("checked", False)}
                for option in item.get("options", [])
            ],
        }
        for item in current
    ]
    print(json.dumps({"recordCount": records(), "controls": summary}, ensure_ascii=False, indent=2))


def filter_spec(active_control, operator):
    return {
        "type": "group",
        "logic": "AND",
        "children": [
            {"type": "condition", "field": active_control, "operator": operator, "value": ["1"]}
        ],
    }


def sort_spec(sequence_control, name_control):
    return {
        "sortCid": sequence_control["controlId"],
        "sortType": 2,
        "moreSort": [
            {
                "controlId": control["controlId"],
                "dataType": control["type"],
                "spliceType": 0,
                "filterType": 0,
                "dateRange": 0,
                "dateRangeType": 0,
                "value": "",
                "values": [],
                "minValue": "",
                "maxValue": "",
                "isAsc": True,
                "dynamicSource": [],
                "advancedSetting": {},
                "isGroup": False,
                "groupFilters": [],
                "emptyRule": 0,
            }
            for control in (sequence_control, name_control)
        ],
    }


def view_list():
    result = run("worksheet", "view", "list", WORKSHEET, "-a", APP)
    return result if isinstance(result, list) else result.get("data", [])


def view_info(view_id):
    result = run("worksheet", "view", "info", WORKSHEET, view_id, "-a", APP)
    return result.get("data", result)


def step_views():
    fields = {control["controlName"]: control for control in live_controls()}
    columns = [fields[name]["controlId"] for name in ("Journal Name", "Type", "Sequence Prefix")]
    sorting = sort_spec(fields["Sequence"], fields["Journal Name"])
    current = view_list()
    print("Backup:", backup("journals_views_pre_views", current))
    by_name = {view["name"]: view["viewId"] for view in current}
    journal_view = by_name.get("Journals") or by_name.get("All") or by_name.get("全部") or DEFAULT_VIEW
    definitions = {
        "Journals": (journal_view, filter_spec(fields["Active"]["controlId"], "eq")),
        "Archived": (by_name.get("Archived"), filter_spec(fields["Active"]["controlId"], "ne")),
    }
    for name, (view_id, filters) in definitions.items():
        spec = {
            "name": name,
            "viewType": "table",
            "filter": filters,
            "tableFields": columns,
        }
        if view_id:
            run("worksheet", "view", "update", WORKSHEET, view_id, "-a", APP,
                "--view-spec", json.dumps(spec))
        else:
            run("worksheet", "view", "create", WORKSHEET, name, "-a", APP,
                "--view-spec", json.dumps(spec))
    by_name = {view["name"]: view["viewId"] for view in view_list()}
    for name in definitions:
        view_id = by_name[name]
        run("worksheet", "view", "update", WORKSHEET, view_id, "-a", APP,
            "--view-json", json.dumps(sorting), "--edit-attrs", "sortCid,sortType,moreSort")
        display = {
            "showControls": columns,
            "advancedSetting": {
                "customdisplay": "1",
                "customShowControls": json.dumps(columns),
            },
        }
        run("worksheet", "view", "update", WORKSHEET, view_id, "-a", APP,
            "--view-json", json.dumps(display),
            "--edit-attrs", "showControls,advancedSetting",
            "--edit-ad-keys", "customdisplay,customShowControls")
        if view_info(view_id).get("name") != name:
            run("worksheet", "view", "update", WORKSHEET, view_id, "-a", APP, "--name", name)
    step_verify_views()


def step_verify_views():
    fields = {control["controlId"]: control["controlName"] for control in live_controls()}
    output = []
    for view in view_list():
        info = view_info(view["viewId"])
        output.append({
            "name": info.get("name"),
            "viewId": view["viewId"],
            "type": info.get("viewType"),
            "columns": [fields.get(control, control) for control in info.get("showControls", [])],
            "sort": [
                {"field": fields.get(sort.get("controlId"), sort.get("controlId")), "ascending": sort.get("isAsc")}
                for sort in info.get("moreSort", [])
            ],
            "filters": info.get("filters", []),
        })
    print(json.dumps(output, ensure_ascii=False, indent=2))


def step_audit():
    current = live_controls()
    names = {control["controlName"] for control in current}
    expected = {control["controlName"] for control in controls()}
    deferred = {
        "Default Account", "Suspense Account", "Private Share Account", "Profit Account", "Loss Account",
        "Currency", "Payment Methods", "Bank Account Number", "Journal Items", "E-invoicing", "Email Alias",
    }
    if names != expected:
        raise SystemExit(f"Field mismatch: expected {sorted(expected)}, got {sorted(names)}")
    if names & deferred:
        raise SystemExit(f"Deferred fields were created unexpectedly: {sorted(names & deferred)}")
    if any(control["type"] == 29 for control in current):
        raise SystemExit("Unexpected Relation field found in the Phase 1 Journals core slice.")
    app = run("app", "info", "-a", APP)["data"]
    section = next(section for section in app["sections"] if section["name"] == "Invoicing")
    item = next(item for item in section["items"] if item["id"] == WORKSHEET)
    rules_result = run("worksheet", "rules", WORKSHEET)
    rules = rules_result if isinstance(rules_result, list) else rules_result.get("data", [])
    actions_result = run("worksheet", "custom-actions", WORKSHEET)
    actions = actions_result if isinstance(actions_result, list) else actions_result.get("data", [])
    audit = {
        "profile": PROFILE,
        "app": app.get("name"),
        "section": section["name"],
        "worksheet": {"id": item["id"], "name": item["name"], "alias": item.get("alias")},
        "recordCount": records(),
        "fieldCount": len(current),
        "fieldTypes": {control["controlName"]: control["type"] for control in current},
        "rules": rules,
        "customActions": actions,
    }
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    step_verify_views()


STEPS = {
    "fields": step_fields,
    "views": step_views,
    "verify": step_verify,
    "verify-views": step_verify_views,
    "audit": step_audit,
}

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    STEPS[step]()
