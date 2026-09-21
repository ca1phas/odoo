# crm.stage — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 21 Sep 2026. Menu: **CRM ▸ Configuration ▸ Stages**. `_order = 'sequence, name, id'`.

## Fields

| Field | Label | Type | Req. | Notes |
|---|---|---|---|---|
| `name` | Stage Name | char | **yes** | placeholder *e.g. Qualification* |
| `sequence` | Sequence | integer | | help "Used to order stages. Lower is better." |
| `is_won` | Is Won Stage? | boolean | | |
| `rotting_threshold_days` | Days to rot | integer | | help "Highlight opportunities that haven't been updated for this many days. Set to 0 to disable." Labelled **Rotting in … days** on the form, hidden when `is_won` |
| `requirements` | Requirements | text | | help "Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name." Its own *Requirements* separator |
| `team_ids` | Sales Teams | **many2many** → `crm.team` | | `widget="many2many_tags"`, placeholder *Show to all teams*, `no_open` + `no_create`. **Hidden when `team_count <= 1`** — a single-team database never sees it |
| `fold` | Folded in Pipeline | boolean | | labelled **Fold by Default** on the form |
| `team_count` | — | integer, computed | | technical, invisible; only decides whether Sales Teams shows |

**`team_ids` is a many2many and it is new-ish** — a stage belongs to *several* teams, or to none, meaning "show
to all teams". There is **no `team_id`** singular on `crm.stage` in 19.4.

## Views

- **Form** `crm.stage.form`: title *Stage Name*; then a two-group grid — left `team_ids` · `is_won` · *Rotting in*
  `rotting_threshold_days` days; right `fold`. Then the **Requirements** separator and the text box.
- **List** `crm.stage.list`, `multi_edit="1"`: sequence (handle) · **Stage Name (read-only)** · Is Won Stage? ·
  Sales Teams · Days to rot (optional, hidden).
- **Search**: Name · Sequence · Is Won Stage? · Sales Teams.

## The records — 4

| id | Stage Name | Sequence | Is Won | Folded | Requirements |
|---|---|---|---|---|---|
| 1 | New | 1 | — | — | — |
| 2 | Qualified | 2 | — | — | — |
| 3 | Proposition | 3 | — | — | — |
| 4 | Won | **70** | **yes** | — | — |

No stage carries a requirement, a rotting threshold or a team on this tenant.
