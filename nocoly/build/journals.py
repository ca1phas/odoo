#!/usr/bin/env python3
"""Build the Journals worksheet (Odoo account.journal, as on casimir.odoo.com saas~19.4) in ERP Master.

Teh Li Wei built the first cut on 15 Sep 2026 (steps fields, views, verify-fields, verify-views, audit); the
gaps against the casimir reference were closed the same day (steps layout, rules, buttons, seed, verify,
selfcheck, check, order, journal, show). Requirements: nocoly/worksheets/05-journals.md. Generic helpers:
common.py. Run from the repo root with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/journals.py fields     # 1. the 7 base controls, on an empty worksheet only (refuses now)
    ~/.hap-venv/bin/python nocoly/build/journals.py layout     # 2. Odoo's form: tabs, the two Dedicated Sequence checkboxes,
                                                               #    positions, help, hints, required; Sequence Prefix at most 5
                                                               #    characters and unique
    ~/.hap-venv/bin/python nocoly/build/journals.py rules      # 3. fields shown by Type; Sequence Prefix length (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/journals.py views      # 4. Journals and Archived tables: columns, sort, quick filter Type
    ~/.hap-venv/bin/python nocoly/build/journals.py buttons    # 5. Archive / Unarchive and their one-step workflows
    ~/.hap-venv/bin/python nocoly/build/journals.py seed       # 6. the 7 journals of the reference (upsert by Sequence Prefix), then verify
    ~/.hap-venv/bin/python nocoly/build/journals.py verify     # compare the live journals with the reference
    ~/.hap-venv/bin/python nocoly/build/journals.py selfcheck  # API writes the rules must refuse, and the two buttons, on TEST Journal
    ~/.hap-venv/bin/python nocoly/build/journals.py check      # read back controls, rules, views and buttons against this spec
    ~/.hap-venv/bin/python nocoly/build/journals.py order      # each view's records, in the order the view sorts them
    ~/.hap-venv/bin/python nocoly/build/journals.py journal "Bank"   # stored values by Journal Name, hidden fields included
    ~/.hap-venv/bin/python nocoly/build/journals.py show       # the live control list
    ~/.hap-venv/bin/python nocoly/build/journals.py verify-fields | verify-views | audit   # the first build's printouts

Profile. hap-cli 0.8.31 picks the account as --profile > $HAP_PROFILE > the active profile (`hap auth accounts`
marks it with *). This script passes nothing unless HAP_PROFILE is set, so it runs on any machine whose active
profile reaches ERP Master; otherwise name the profile, e.g. on the colleague's machine

    HAP_PROFILE=fbmy-nocoly ~/.hap-venv/bin/python nocoly/build/journals.py check

Every write step first reads the live worksheet and stops if the profile does not reach ERP Master, or if Journals
holds controls, option keys, rules, buttons, views or records that neither the first build nor this script made.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import common as C
import hap

PROFILE = os.environ.get("HAP_PROFILE") or None     # None: hap-cli's active profile
APP = "6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9"
WORKSHEET = "6aa8f5191204328eb1af162a"
DEFAULT_VIEW = "6aa8f5191204328eb1af162e"
HERE = Path(__file__).resolve().parent
BACKUPS = HERE / "backups"
KEY = "Journals: "                                  # ids.json key prefix for everything this worksheet owns


def run(*args):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    command = ["hap", *(["--profile", PROFILE] if PROFILE else []), "--json", *args]
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
    """The first build's seven controls (client-side ids), for `fields` on an empty worksheet."""
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
        step_verify_fields()
        return
    if len(current) > 3:
        raise SystemExit(f"Unexpected existing controls; refusing to replace them: {sorted(names)}")
    print("Backup:", backup("journals_controls_pre_fields", current))
    run("worksheet", "update-fields", WORKSHEET, "--controls", json.dumps(controls(), ensure_ascii=False))
    step_verify_fields()


def step_verify_fields():
    """The first build's control printout (its `verify` step until 15 Sep 2026)."""
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


# ── guard: what may be on the worksheet ─────────────────────────────────────

# The first build as it stood live at commit 24fdefc (Teh Li Wei, 15 Sep 2026): control ids and option keys
# are kept by every step here.
FIRST_BUILD = {
    "6aa8f6c81204328eb1af1676": ("Journal Name", 2),
    "6aa8f6c81204328eb1af1677": ("Sequence Prefix", 2),
    "6aa8f6c81204328eb1af1678": ("Type", 11),
    "6aa8f6c81204328eb1af1679": ("Communication Type", 11),
    "6aa8f6c81204328eb1af167a": ("Communication Standard", 11),
    "6aa8f6c81204328eb1af167b": ("Active", 36),
    "6aa8f6c81204328eb1af167c": ("Sequence", 6),
}
OPTIONS = {
    "Type": TYPE_OPTIONS,
    "Communication Type": COMMUNICATION_TYPE_OPTIONS,
    "Communication Standard": COMMUNICATION_STANDARD_OPTIONS,
}
TEST_PREFIX = "TEST"


def guard():
    """Stop unless the profile reaches ERP Master and Journals holds only the first build and this script's work.

    Returns the live controls."""
    who = run("auth", "whoami")
    app = run("app", "info", "-a", APP).get("data", {})
    section = next((s for s in app.get("sections", []) if any(i["id"] == WORKSHEET for i in s["items"])), None)
    if app.get("name") != "ERP Master" or not section or section["name"] != "Invoicing":
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › Invoicing › Journals")
    problems = []
    ctrls = live_controls()
    by_id = {c["controlId"]: c for c in ctrls}
    for cid, (name, kind) in FIRST_BUILD.items():
        c = by_id.get(cid)
        if not c or (c["controlName"], c["type"]) != (name, kind):
            problems.append(f"first-build control {cid} ({name}) is {c and (c['controlName'], c['type'])}")
    known = {name for name, _ in FIRST_BUILD.values()} | set(NEW)
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c["controlName"] not in known]
    names = hap.by_name(ctrls)
    for name, opts in OPTIONS.items():
        live = [(o["key"], o["value"]) for o in names.get(name, {}).get("options", []) if not o.get("isDeleted")]
        if live != [(o["key"], o["value"]) for o in opts]:
            problems.append(f"{name} options changed: {live}")
    rules = {r["name"] for r in hap.listing("worksheet", "rules", WORKSHEET)}
    problems += [f"unknown rule {n!r}" for n in rules - set(RULE_NAMES)]
    buttons = {b["name"] for b in hap.listing("worksheet", "custom-actions", WORKSHEET)}
    problems += [f"unknown button {n!r}" for n in buttons - {"Archive", "Unarchive"}]
    views = {v["name"] for v in hap.listing("worksheet", "view", "list", WORKSHEET, "-a", APP)}
    problems += [f"unknown view {n!r}" for n in views - {"Journals", "Archived"}]
    if "Journal Name" in names:
        title, prefix = names["Journal Name"]["controlId"], names["Sequence Prefix"]["controlId"]
        codes = {r.get(prefix): r.get(title) for r in C.records(WORKSHEET, APP)}
        problems += [f"unknown record {n!r} ({code})" for code, n in codes.items()
                     if code not in reference_table() and not str(n).startswith(TEST_PREFIX)]
    if problems:
        sys.exit("Journals differs from the first build plus this script's work — stopping:\n  "
                 + "\n  ".join(problems))
    print(f"  guard: profile {who.get('profile')!r}, ERP Master › Invoicing › Journals, {len(ctrls)} controls, "
          f"{len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


# ── 2 · layout ──────────────────────────────────────────────────────────────

JOURNAL_ENTRIES, ADVANCED = "Journal Entries", "Advanced Settings"
# Odoo saas~19.4 view_account_journal_form on HAP's 12-column grid: name; Type and Sequence Prefix; the
# notebook pages Journal Entries (the two dedicated sequences) and Advanced Settings (Payment Communications).
# Sequence is not on Odoo's form: it is the list's drag handle, and HAP rows cannot be dragged.
PLACE = {  # name -> (row, col, size, tab)
    "Journal Name": (0, 0, 12, None),
    "Type": (1, 0, 6, None), "Sequence Prefix": (1, 1, 6, None),
    "Sequence": (2, 0, 6, None),
    JOURNAL_ENTRIES: (3, 0, 12, None),
    "Dedicated Credit Note Sequence": (4, 0, 6, JOURNAL_ENTRIES),
    "Dedicated Payment Sequence": (5, 0, 6, JOURNAL_ENTRIES),
    ADVANCED: (6, 0, 12, None),
    "Communication Type": (7, 0, 6, ADVANCED),
    "Communication Standard": (8, 0, 6, ADVANCED),
    "Active": (9, 0, 6, None),
}
HINTS = {"Sequence Prefix": "e.g. INV"}           # Odoo's only static placeholder on this form
DESC = {  # Odoo field help (account_journal.py)
    "Type": "Select 'Sale' for customer invoices journals.\n"
            "Select 'Purchase' for vendor bills journals.\n"
            "Select 'Cash', 'Bank' or 'Credit Card' for journals that are used in customer or vendor payments.\n"
            "Select 'General' for miscellaneous operations journals.",
    "Sequence Prefix": "Shorter name used for display. The journal entries of this journal will also be named "
                       "using this prefix by default.",
    "Sequence": "Used to order Journals in the dashboard view",
    "Active": "Set active to false to hide the Journal without removing it.",
    "Communication Type": "You can set here the default communication that will appear on customer invoices, once "
                          "validated, to help the customer to refer to that particular invoice when making the "
                          "payment.",
    "Communication Standard": "You can choose different models for each type of reference. The default one is the "
                              "Odoo reference.",
    "Dedicated Credit Note Sequence": "Check this box if you don't want to share the same sequence for invoices and "
                                      "credit notes made from this journal",
    "Dedicated Payment Sequence": "Check this box if you don't want to share the same sequence on payments and bank "
                                  "transactions posted on this journal",
}
REQUIRED = {"Journal Name", "Type", "Sequence Prefix", "Communication Type", "Communication Standard"}
HIDDEN = {"Active"}
CODE_SIZE = 5                                     # Odoo code = fields.Char(size=5)
# Controls this script adds: (kind, alias, advancedSetting)
NEW = {
    JOURNAL_ENTRIES: ("SECTION", "", {}),
    ADVANCED: ("SECTION", "", {}),
    "Dedicated Credit Note Sequence": ("SWITCH", "refund_sequence", {"defsource": default(0), "showtype": "0"}),
    "Dedicated Payment Sequence": ("SWITCH", "payment_sequence", {"defsource": default(0), "showtype": "0"}),
}
# Settings this script owns on existing controls, besides place, hint, help, required and visibility.
SETTINGS = {
    "Sequence Prefix": {"unique": True,
                        "advancedSetting": {"checkrange": "1", "min": "", "max": str(CODE_SIZE)}},
}


def desired(c, tab_ids):
    """The attributes `layout` owns on control c, as they should read back."""
    name = c["controlName"]
    row, col, size, tab = PLACE[name]
    want = {"row": row, "col": col, "size": size, "sectionId": tab_ids.get(tab, "") if tab else ""}
    if c["type"] == C.TAB:
        return want
    want.update(hint=HINTS.get(name, ""), desc=DESC.get(name, ""), required=name in REQUIRED,
                fieldPermission="011" if name in HIDDEN else "111")
    want.update({k: v for k, v in SETTINGS.get(name, {}).items() if k != "advancedSetting"})
    return want


def desired_advanced(name):
    return {**NEW.get(name, ("", "", {}))[2], **SETTINGS.get(name, {}).get("advancedSetting", {})}


def layout_differences(ctrls):
    tab_ids = {c["controlName"]: c["controlId"] for c in ctrls if c["type"] == C.TAB}
    out = {}
    for c in ctrls:
        want = desired(c, tab_ids)
        diff = {k: (c.get(k), v) for k, v in want.items() if c.get(k) != v}
        adv = c.get("advancedSetting") or {}
        diff.update({f"advancedSetting.{k}": (adv.get(k), v) for k, v in desired_advanced(c["controlName"]).items()
                     if adv.get(k) != v})
        if diff:
            out[c["controlName"]] = diff
    return out


def step_layout():
    ctrls = guard()
    print("  backup:", backup("journals_controls_pre_layout", ctrls))
    names = {c["controlName"] for c in ctrls}
    missing = [n for n in NEW if n not in names]
    if missing:
        for name in missing:
            kind, alias, adv = NEW[name]
            row, col, size, _ = PLACE[name]
            ctrls.append(C.control(kind, name, (row, col, size), alias=alias, hint="" if kind != "SECTION" else None,
                                   desc=DESC.get(name), advanced_setting=adv or None))
        run("worksheet", "update-fields", WORKSHEET, "--controls", json.dumps(ctrls, ensure_ascii=False))
        ctrls = live_controls()
        print(f"  added: {missing}")
    tab_ids = {c["controlName"]: c["controlId"] for c in ctrls if c["type"] == C.TAB}
    changed = layout_differences(ctrls)
    for c in ctrls:
        if c["controlName"] in changed:
            c.update(desired(c, tab_ids))
            c["advancedSetting"] = {**(c.get("advancedSetting") or {}), **desired_advanced(c["controlName"])}
    if changed:
        run("worksheet", "update-fields", WORKSHEET, "--controls", json.dumps(ctrls, ensure_ascii=False))
        print("  updated:", json.dumps(changed, ensure_ascii=False))
    ctrls = live_controls()
    left = layout_differences(ctrls)
    if left:
        sys.exit(f"layout read back with differences: {json.dumps(left, ensure_ascii=False)}")
    lost = [cid for cid in FIRST_BUILD if cid not in {c['controlId'] for c in ctrls}]
    if lost:
        sys.exit(f"first-build control ids missing after the save: {lost}")
    for c in ctrls:
        if c["controlName"] in NEW:
            C.remember("controls", KEY + c["controlName"], c["controlId"])
    show()


# ── 3 · rules ───────────────────────────────────────────────────────────────

RULE_SALES_PURCHASE = "Dedicated Credit Note Sequence only for Sales and Purchase"
RULE_LIQUIDITY = "Dedicated Payment Sequence only for Bank, Cash and Credit Card"
RULE_ENTRIES_TAB = "Journal Entries tab only for Sales, Purchase, Bank, Cash and Credit Card"
RULE_COMMUNICATIONS = "Payment Communications only for Sales"
RULE_NAMES = [RULE_SALES_PURCHASE, RULE_LIQUIDITY, RULE_ENTRIES_TAB, RULE_COMMUNICATIONS]


def type_in(f, *labels):
    """Condition: Type is any of the labels (EQ with several option keys)."""
    keys = [o["key"] for o in f["Type"]["options"] if o["value"] in labels]
    if len(keys) != len(labels):
        sys.exit(f"Type options {labels} not all found")
    return {"controlId": f["Type"]["controlId"], "dataType": f["Type"]["type"], "spliceType": 1,
            "filterType": C.EQ, "value": "", "values": keys, "dynamicSource": [], "isGroup": False}


def step_rules():
    guard()
    ctrls = live_controls()
    f = hap.by_name(ctrls)
    rules = [  # (name, type, filters, items, options) — show rules hide their fields while Type is empty
        # <field name="refund_sequence" invisible="type not in ['sale', 'purchase']"/>
        (RULE_SALES_PURCHASE, C.INTERACTION, C.any_of([type_in(f, "Sales", "Purchase")]),
         [C.item(C.SHOW, f["Dedicated Credit Note Sequence"])], {}),
        # <field name="payment_sequence" invisible="type not in ('bank', 'cash', 'credit')"/>
        (RULE_LIQUIDITY, C.INTERACTION, C.any_of([type_in(f, "Cash", "Bank", "Credit Card")]),
         [C.item(C.SHOW, f["Dedicated Payment Sequence"])], {}),
        # the page holds only the two dedicated sequences until Chart of Accounts adds its accounts
        (RULE_ENTRIES_TAB, C.INTERACTION,
         C.any_of([type_in(f, "Sales", "Purchase", "Cash", "Bank", "Credit Card")]),
         [C.item(C.SHOW, f[JOURNAL_ENTRIES])], {}),
        # <group string="Payment Communications" invisible="type != 'sale'"> — the only content of Advanced
        # Settings until Self Billing, Email Alias and Send Copy To are built
        (RULE_COMMUNICATIONS, C.INTERACTION, C.any_of([type_in(f, "Sales")]),
         [C.item(C.SHOW, f[ADVANCED], f["Communication Type"], f["Communication Standard"])], {}),
    ]
    C.upsert_rules(WORKSHEET, rules, "journals_rules_pre_rules")
    for r in hap.listing("worksheet", "rules", WORKSHEET):
        C.remember("rules", KEY + r["name"], r["ruleId"])


# ── 4 · views ───────────────────────────────────────────────────────────────

def filter_spec(active_control, operator):
    return {
        "type": "group",
        "logic": "AND",
        "children": [
            {"type": "condition", "field": active_control, "operator": operator, "value": ["1"]}
        ],
    }


def sort_spec(*sort_controls):
    """Ascending on the controls, in order (the first build passed Sequence and Journal Name)."""
    return {
        "sortCid": sort_controls[0]["controlId"],
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
            for control in sort_controls
        ],
    }


def view_list():
    result = run("worksheet", "view", "list", WORKSHEET, "-a", APP)
    return result if isinstance(result, list) else result.get("data", [])


def view_info(view_id):
    result = run("worksheet", "view", "info", WORKSHEET, view_id, "-a", APP)
    return result.get("data", result)


def step_views():
    """Journals and Archived tables. Odoo's list: Journal Name, Type, Sequence Prefix (Default Account waits for
    Chart of Accounts); _order 'sequence, type, code'; search filters Sales · Purchases · Liquidity ·
    Miscellaneous, here one Type quick filter that takes several types (Liquidity = Cash + Bank + Credit Card)."""
    guard()
    fields = {control["controlName"]: control for control in live_controls()}
    columns = [fields[name]["controlId"] for name in ("Journal Name", "Type", "Sequence Prefix")]
    sorting = sort_spec(fields["Sequence"], fields["Type"], fields["Sequence Prefix"])
    quick = [{"fieldId": fields["Type"]["controlId"], "selectionType": "multiple", "displayType": "dropdown"}]
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
            "quickFilters": quick,
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
        C.remember("views", KEY + name, view_id)
    print("  order:", C.sort_views(WORKSHEET, APP, list(definitions)))
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
            "quickFilters": [
                {"field": fields.get(q.get("controlId"), q.get("controlId")), **(q.get("advancedSetting") or {})}
                for q in info.get("fastFilters", [])
            ],
        })
    print(json.dumps(output, ensure_ascii=False, indent=2))


def step_audit():
    current = live_controls()
    names = {control["controlName"] for control in current}
    expected = set(PLACE)
    deferred = {
        "Default Account", "Suspense Account", "Private Share Account", "Profit Account", "Loss Account",
        "Currency", "Payment Methods", "Bank Account Number", "Journal Items", "E-invoicing", "Email Alias",
        "Ledger", "Bank Feeds", "Self Billing", "Send Copy To", "Invoice report", "Show journal on dashboard",
        "Color Index", "Secure Posted Entries with Hash",
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
        "profile": PROFILE or run("auth", "whoami").get("profile"),
        "app": app.get("name"),
        "section": section["name"],
        "worksheet": {"id": item["id"], "name": item["name"], "alias": item.get("alias")},
        "recordCount": records(),
        "fieldCount": len(current),
        "fieldTypes": {control["controlName"]: control["type"] for control in current},
        "rules": [{"name": r["name"], "ruleId": r["ruleId"], "type": r["type"], "disabled": r["disabled"]}
                  for r in rules],
        "customActions": [{"name": a["name"], "btnId": a["btnId"]} for a in actions],
    }
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    step_verify_views()


# ── 5 · buttons ─────────────────────────────────────────────────────────────

MSG_ARCHIVE = "Are you sure that you want to archive this record?"


def step_buttons():
    guard()
    active = C.fields(WORKSHEET)["Active"]["controlId"]
    when = lambda op: {"type": "group", "logic": "AND", "children": [
        {"type": "condition", "field": active, "operator": op, "value": ["1"]}]}
    buttons = [  # Odoo ⚙ Actions › Archive / Unarchive, as on Contacts, Units & Packagings and Products
        ({"name": "Archive", "type": "triggerWorkflow", "enableWhen": when("eq"), "isBatch": True,
          "confirm": True, "confirmMsg": MSG_ARCHIVE, "sureName": "Archive", "cancelName": "Cancel"},
         [{"fieldId": active, "value": "0"}], "Archive the journal"),
        ({"name": "Unarchive", "type": "triggerWorkflow", "enableWhen": when("ne"), "isBatch": True},
         [{"fieldId": active, "value": "1"}], "Unarchive the journal"),
    ]
    C.upsert_buttons(WORKSHEET, APP, buttons, KEY, "journals_buttons_pre_buttons")
    for key in (KEY + "Archive", KEY + "Unarchive"):
        print(C.structure(hap.ids()["workflows"][key]))


# ── 6 · seed and verify ─────────────────────────────────────────────────────

REFERENCE = HERE.parent / "reference" / "odoo-19.4" / "account.journal.md"
TYPES = [o["value"] for o in TYPE_OPTIONS]


def reference_table():
    """The journals of the 19.4 extract by Sequence Prefix, in Odoo id order (table "Records")."""
    out, section = {}, ""
    for line in REFERENCE.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            section = line.strip("# ")
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if section.startswith("Records") and len(cells) == 13 and cells[2] in TYPES:
            out[cells[3]] = dict(id=int(cells[0]), name=cells[1], type=cells[2], code=cells[3],
                                 sequence=int(cells[4]), invoice_reference_type=cells[5],
                                 invoice_reference_model=cells[6], refund_sequence=cells[7] == "yes",
                                 payment_sequence=cells[8] == "yes", active="all active" in section)
    return dict(sorted(out.items(), key=lambda kv: kv[1]["id"]))


def listed(v):
    """A record-get option value (a list, or a JSON string of one) as a list."""
    if isinstance(v, str):
        v = json.loads(v) if v.startswith("[") else []
    return v if isinstance(v, list) else []


def option_label(v):
    labels = [x.get("value") if isinstance(x, dict) else x for x in listed(v)]
    return labels[0] if labels else None


def read_journal(rowid):
    """One journal through `record get` (by alias); `record list` can return hidden fields empty."""
    d = hap.run("worksheet", "record", "get", WORKSHEET, rowid, "-a", APP)["data"]
    flag = lambda k: str(d.get(k)) in ("1", "True", "true")
    number = d.get("sequence")
    return dict(rowid=rowid, name=d.get("name"), type=option_label(d.get("type")), code=d.get("code") or "",
                sequence=int(float(number)) if number not in (None, "") else None,
                invoice_reference_type=option_label(d.get("invoice_reference_type")),
                invoice_reference_model=option_label(d.get("invoice_reference_model")),
                refund_sequence=flag("refund_sequence"), payment_sequence=flag("payment_sequence"),
                active=flag("active"))


def read_journals():
    """Every journal, archived or not, by rowid."""
    return {r["rowid"]: read_journal(r["rowid"]) for r in C.records(WORKSHEET, APP)}


def standard_label(short):
    """'Full Reference' (the extract's short form) -> 'Full Reference (INV/2024/00001)'."""
    return next(o["value"] for o in COMMUNICATION_STANDARD_OPTIONS if o["value"].split(" (")[0] == short)


def expected(e):
    return dict(name=e["name"], type=e["type"], code=e["code"], sequence=e["sequence"],
                invoice_reference_type=e["invoice_reference_type"],
                invoice_reference_model=standard_label(e["invoice_reference_model"]),
                refund_sequence=e["refund_sequence"], payment_sequence=e["payment_sequence"], active=e["active"])


def differences(live, e):
    return {k: (live.get(k), v) for k, v in expected(e).items() if live.get(k) != v}


def values_for(f, e):
    key = lambda name, label: next(o["key"] for o in f[name]["options"] if o["value"] == label)
    want = expected(e)
    cid = lambda n: f[n]["controlId"]
    return [{"id": cid("Journal Name"), "value": want["name"]},
            {"id": cid("Type"), "value": [key("Type", want["type"])]},
            {"id": cid("Sequence Prefix"), "value": want["code"]},
            {"id": cid("Sequence"), "value": str(want["sequence"])},
            {"id": cid("Communication Type"), "value": [key("Communication Type", want["invoice_reference_type"])]},
            {"id": cid("Communication Standard"),
             "value": [key("Communication Standard", want["invoice_reference_model"])]},
            {"id": cid("Dedicated Credit Note Sequence"), "value": 1 if want["refund_sequence"] else 0},
            {"id": cid("Dedicated Payment Sequence"), "value": 1 if want["payment_sequence"] else 0},
            {"id": cid("Active"), "value": 1 if want["active"] else 0}]    # always explicit on API writes


def step_seed(*only):
    """Create the missing journals and correct the ones that differ, matched by Sequence Prefix; `only` limits it
    to Sequence Prefixes. Creation follows Odoo's ids."""
    guard()
    f = C.fields(WORKSHEET)
    journals = {j["code"]: j for j in read_journals().values()}
    backup("journals_records_pre_seed", journals)
    for code, e in reference_table().items():
        if only and code not in only:
            continue
        live = journals.get(code)
        if live and not differences(live, e):
            continue
        values = json.dumps(values_for(f, e), ensure_ascii=False)
        if live:
            hap.run("worksheet", "record", "update", WORKSHEET, live["rowid"], "-a", APP, "--fields-json", values)
            rowid = live["rowid"]
            print(f"  updated {code} {e['name']}")
        else:
            rowid = C.row_id(hap.run("worksheet", "record", "create", WORKSHEET, "-a", APP, "--fields-json", values))
            print(f"  created {code} {e['name']}: {rowid}")
        got = read_journal(rowid)
        if differences(got, e):
            sys.exit(f"{code}: read back {differences(got, e)}")
    step_verify(*only)


def step_verify(*only):
    """Compare the live journals with the 19.4 extract, field by field."""
    reference = reference_table()
    journals = {j["code"]: j for j in read_journals().values()}
    bad = 0
    for code, e in reference.items():
        if only and code not in only:
            continue
        live = journals.get(code)
        if not live:
            print(f"  MISSING  {code:<5} {e['name']}")
            bad += 1
            continue
        diffs = differences(live, e)
        bad += bool(diffs)
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {code:<5} {live['name']:<25} {live['type']:<13} "
              f"seq={live['sequence']:<3} {live['invoice_reference_type']} / {live['invoice_reference_model']} "
              f"credit-note-seq={int(live['refund_sequence'])} payment-seq={int(live['payment_sequence'])} "
              f"active={int(live['active'])}" + (f"  <- {diffs}" if diffs else ""))
    extra = sorted(f"{j['name']} ({code}, active={int(j['active'])})" for code, j in journals.items()
                   if code not in reference)
    print(f"  {len(reference)} in the extract; {bad} missing or differing; {len(extra)} not in the extract {extra}")
    return bad


def step_journal(*names):
    """Print the stored values of journals by Journal Name, hidden fields included."""
    journals = {j["name"]: j for j in read_journals().values()}
    for name in names or sorted(journals):
        j = journals.get(name)
        print(f"  {name}: " + (json.dumps(j, ensure_ascii=False) if j else "no such journal"))


def step_order():
    """Each view's records in the order the view returns them (its own filter and sort)."""
    f = C.fields(WORKSHEET)
    name, code = f["Journal Name"]["controlId"], f["Sequence Prefix"]["controlId"]
    sequences = {j["rowid"]: j["sequence"] for j in read_journals().values()}
    for v in hap.listing("worksheet", "view", "list", WORKSHEET, "-a", APP):
        res = hap.run("worksheet", "record", "list", WORKSHEET, "-a", APP, "-n", "100", "--view-id", v["viewId"],
                      "--use-field-id-as-key")
        data = res.get("data", res) if isinstance(res, dict) else res
        rows = (data.get("rows") if isinstance(data, dict) else data) or []
        print(f"  {v['name']} ({len(rows)}): "
              + ", ".join(f"{r[name]} [{r[code]}, {sequences.get(r['rowid'])}]" for r in rows))


# ── self-check: API writes and buttons ──────────────────────────────────────

TEST_JOURNAL = dict(id=0, name="TEST Journal", type="Miscellaneous", code="TEST", sequence=99,
                    invoice_reference_type="Based on Invoice", invoice_reference_model="Full Reference",
                    refund_sequence=False, payment_sequence=False, active=True)


def attempt(label, *args):
    """Run a write expected to be refused; return (refused, message)."""
    try:
        out = hap.run(*args)
    except RuntimeError as error:
        return True, str(error)
    data = out.get("data", out) if isinstance(out, dict) else {}
    code = (out or {}).get("resultCode") if isinstance(out, dict) else None
    inner = data.get("resultCode") if isinstance(data, dict) else None
    return (code not in (None, 1) or inner not in (None, 1)), json.dumps(out, ensure_ascii=False)[:400]


def step_selfcheck():
    """Writes through the API that Journals must refuse, then Archive and Unarchive on TEST Journal.

    Uses one record, TEST Journal (TEST, Miscellaneous, Sequence 99), created if missing and left archived.
    A write that is not refused is undone (a created record gets a TEST code and is archived) and reported."""
    guard()
    f = C.fields(WORKSHEET)
    journals = read_journals()
    test = next((j for j in journals.values() if j["name"] == TEST_JOURNAL["name"]), None)
    if not test:
        rowid = C.row_id(hap.run("worksheet", "record", "create", WORKSHEET, "-a", APP, "--fields-json",
                                 json.dumps(values_for(f, TEST_JOURNAL), ensure_ascii=False)))
        test = read_journal(rowid)
        print(f"  created TEST Journal: {rowid}")
    rowid = test["rowid"]
    prefix = f["Sequence Prefix"]["controlId"]
    too_long = "TSTLNG"
    results = []

    def create(label, code):
        values = values_for(f, {**TEST_JOURNAL, "name": f"TEST {label}", "code": code})
        refused, message = attempt(label, "worksheet", "record", "create", WORKSHEET, "-a", APP,
                                   "--fields-json", json.dumps(values, ensure_ascii=False))
        if not refused:
            stray = next(j for j in read_journals().values() if j["name"] == f"TEST {label}")
            hap.run("worksheet", "record", "update", WORKSHEET, stray["rowid"], "-a", APP, "--fields-json",
                    json.dumps([{"id": prefix, "value": f"T{stray['rowid'][:4]}"},
                                {"id": f["Active"]["controlId"], "value": 0}]))
            message += f"  -> NOT refused: TEST {label} ({stray['rowid']}) recoded and archived"
        results.append((f"create with Sequence Prefix {code!r}", refused, message))

    def update(label, code):
        refused, message = attempt(label, "worksheet", "record", "update", WORKSHEET, rowid, "-a", APP,
                                   "--fields-json", json.dumps([{"id": prefix, "value": code}]))
        now = read_journal(rowid)["code"]
        if now != TEST_JOURNAL["code"]:
            hap.run("worksheet", "record", "update", WORKSHEET, rowid, "-a", APP, "--fields-json",
                    json.dumps([{"id": prefix, "value": TEST_JOURNAL["code"]}]))
            message += f"  -> stored {now!r}; restored {TEST_JOURNAL['code']!r}"
        results.append((f"update TEST Journal's Sequence Prefix to {code!r}", refused, message))

    create("duplicate prefix", "INV")
    create("long prefix", too_long)
    update("duplicate prefix", "BILL")
    update("long prefix", too_long)
    for check, refused, message in results:
        print(f"  {'refused' if refused else 'ACCEPTED'}  {check}\n      {message}")

    active = lambda: read_journal(rowid)["active"]
    workflows = hap.ids()["workflows"]
    for step, want in (("Unarchive", True), ("Archive", False), ("Unarchive", True), ("Archive", False)):
        if active() == want:
            continue
        hap.run("workflow", "trigger", workflows[KEY + step], "-s", rowid)
        for _ in range(20):
            if active() == want:
                break
            time.sleep(1)
        print(f"  workflow trigger {step}: TEST Journal active={int(active())} (expected {int(want)})")
    print(f"  TEST Journal {rowid}: {read_journal(rowid)}")


# ── check: read back the configuration ──────────────────────────────────────

def step_check():
    """Controls, rules, views and buttons against this spec; exits non-zero on a difference."""
    ctrls = live_controls()
    f = hap.by_name(ctrls)
    problems = []
    if set(f) != set(PLACE):
        problems.append(f"controls {sorted(set(f) ^ set(PLACE))}")
    problems += [f"{n}: {d}" for n, d in layout_differences([c for c in ctrls if c["controlName"] in PLACE]).items()]
    for cid, (name, _) in FIRST_BUILD.items():
        if f.get(name, {}).get("controlId") != cid:
            problems.append(f"{name} id is {f.get(name, {}).get('controlId')}, first build {cid}")
    for name, opts in OPTIONS.items():
        live = [(o["key"], o["value"]) for o in f[name]["options"] if not o.get("isDeleted")]
        if live != [(o["key"], o["value"]) for o in opts]:
            problems.append(f"{name} options {live}")
    defaults = {"Communication Type": "Based on Invoice", "Communication Standard": "Full Reference (INV/2024/00001)",
                "Active": "1", "Sequence": "10", "Dedicated Credit Note Sequence": "0",
                "Dedicated Payment Sequence": "0"}
    for name, want in defaults.items():
        source = json.loads(f[name]["advancedSetting"].get("defsource") or "[]")
        value = source[0]["staticValue"] if source else None
        label = next((o["value"] for o in f[name].get("options", []) if o["key"] == value), value)
        if label != want:
            problems.append(f"{name} default {label!r}, want {want!r}")
    if f["Journal Name"].get("attribute") != 1:
        problems.append("Journal Name is not the title field")
    rules = {r["name"]: r for r in hap.listing("worksheet", "rules", WORKSHEET)}
    names = {c["controlId"]: c["controlName"] for c in ctrls}
    keys = {o["key"]: o["value"] for o in f["Type"]["options"]}
    want_rules = {
        RULE_SALES_PURCHASE: (["Sales", "Purchase"], ["Dedicated Credit Note Sequence"]),
        RULE_LIQUIDITY: (["Cash", "Bank", "Credit Card"], ["Dedicated Payment Sequence"]),
        RULE_ENTRIES_TAB: (["Sales", "Purchase", "Cash", "Bank", "Credit Card"], [JOURNAL_ENTRIES]),
        RULE_COMMUNICATIONS: (["Sales"], [ADVANCED, "Communication Type", "Communication Standard"]),
    }
    for name, (types, targets) in want_rules.items():
        r = rules.get(name)
        if not r:
            problems.append(f"rule {name!r} missing")
            continue
        conds = [g for group in r["filters"] for g in group.get("groupFilters", [])]
        got_types = [keys.get(v) for c in conds for v in c.get("values", [])]
        got_targets = [names.get(c["controlId"]) for i in r["ruleItems"] for c in i["controls"]]
        got_kinds = {i["type"] for i in r["ruleItems"]}
        if (r["type"], r["disabled"], got_kinds, got_types, got_targets) != (0, False, {C.SHOW}, types, targets):
            problems.append(f"rule {name!r}: type={r['type']} disabled={r['disabled']} items={got_kinds} "
                            f"types={got_types} targets={got_targets}")
    views = {v["name"]: view_info(v["viewId"]) for v in view_list()}
    columns = ["Journal Name", "Type", "Sequence Prefix"]
    sort = ["Sequence", "Type", "Sequence Prefix"]
    for name, op in (("Journals", 2), ("Archived", 6)):
        v = views.get(name, {})
        got = dict(columns=[names.get(x) for x in v.get("showControls", [])],
                   sort=[(names.get(s["controlId"]), s["isAsc"]) for s in v.get("moreSort", [])],
                   sortCid=names.get(v.get("sortCid")), sortType=v.get("sortType"),
                   filters=[(names.get(x["controlId"]), x["filterType"], x.get("values")) for x in v.get("filters", [])],
                   quick=[(names.get(q["controlId"]), (q.get("advancedSetting") or {}).get("allowitem"))
                          for q in v.get("fastFilters", [])])
        want = dict(columns=columns, sort=[(s, True) for s in sort], sortCid="Sequence", sortType=2,
                    filters=[("Active", op, ["1"])], quick=[("Type", "2")])
        if got != want:
            problems.append(f"view {name}: {got}")
    if [v["name"] for v in view_list()] != ["Journals", "Archived"]:
        problems.append(f"view order {[v['name'] for v in view_list()]}")
    buttons = {b["name"]: b for b in hap.listing("worksheet", "custom-actions", WORKSHEET)}
    for name, op, confirm in (("Archive", 2, MSG_ARCHIVE), ("Unarchive", 6, "")):
        b = buttons.get(name)
        if not b:
            problems.append(f"button {name} missing")
            continue
        conds = [(names.get(x["controlId"]), x["filterType"], x.get("values")) for x in b.get("filters") or []]
        if conds != [("Active", op, ["1"])] or (b.get("confirmMsg") or "") != confirm:
            problems.append(f"button {name}: filters={conds} confirm={b.get('confirmMsg')!r}")
    print("  check: " + ("OK — controls, options, defaults, rules, views and buttons as specified"
                         if not problems else "DIFFERENCES\n    " + "\n    ".join(problems)))
    return len(problems)


def show():
    C.show(WORKSHEET)


STEPS = {
    "fields": step_fields,
    "layout": step_layout,
    "rules": step_rules,
    "views": step_views,
    "buttons": step_buttons,
    "seed": step_seed,
    "verify": step_verify,
    "selfcheck": step_selfcheck,
    "check": step_check,
    "order": step_order,
    "journal": step_journal,
    "show": show,
    "verify-fields": step_verify_fields,
    "verify-views": step_verify_views,
    "audit": step_audit,
}

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "check"
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ("verify", "check") and result:
        sys.exit(1)
