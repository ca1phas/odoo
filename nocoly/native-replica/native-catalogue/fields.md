# Native field types (Nocoly HAP): catalogue for the Odoo rebuild

| | |
|---|---|
| Purpose | Every field type in the Nocoly HAP field designer today, with its settings, tried live, so that each Odoo field kind maps to a native HAP field |
| Rule | Native first (Li Wei, 23 Nov 2026). Try the native option before designing; custom fields and Compute only where no native field fits |
| Status | Survey, 23 Nov 2026, about 14:20–15:25 MYT. Only the probe sheet was changed. Nothing was deleted |
| Target app | Odoo Replica (AI) `<uuid>`, Nocoly SaaS, CLI profile `<profile>`, hap-cli 0.9.14, English UI |
| Probe sheet | **Native Field Probe** `<id>`, alias `x_system__native_probe`, group System Tables `<id>`. 62 fields (inventory in §10). One record, `TEST probe` (`<uuid>`) |
| Companion | `workflow-nodes.md` (native workflow triggers and nodes) |

**Evidence tags**

| Tag | Source | What it proves |
|---|---|---|
| [UI] | Field designer or record form, opened and clicked on 23 Nov 2026 | The setting exists and what it offers |
| [Raw] | `hap --profile <profile> --json worksheet fields <id> --raw`, after saving the designer | The keys a setting is stored in |
| [Rec] | `worksheet record get` of `TEST probe`, entered in the UI | What the platform stores, and the API's view of it |
| [CLI] | `hap worksheet field-types` | The CLI's names and type numbers |
| [Earlier] | `../00-foundation-build/BUILD-LOG.md` and saved notes | Seen before today, not re-tested |
| [Inferred] | Pattern from neighbouring values | Not set and read back |
| [Design] | A proposal in this file | Not tested |

## 1. Odoo field kind → native HAP choice

| Odoo field kind | Native HAP choice (type id) | Key settings | Notes |
|---|---|---|---|
| `char` | **Text**, single line (2, `enumDefault 2`) | Required, no duplicates, character limit, input-format regex, mask, encryption | Mobile scan input for codes |
| `text` | **Text**, multiple lines (2, `enumDefault 1`) | Character limit | No mask or encryption in this mode |
| `html` | **Rich Text** (41) | Default value, required | Stored as HTML. Markdown text (2, `enumDefault 3`) for light notes |
| `integer` / `float`, with a unit | **Number** (6) | `dot` decimals, unit as prefix/suffix text, thousand separator, clamp min–max | The unit is fixed text on the field; there is no unit-of-measure conversion. UoM stays a relation |
| float shown as % (probability) | **Number**, "Display as Percentage", or **Progress bar** input | `numshow 1` | Stores a fraction: 15 % is saved as 0.15 [Rec] |
| `monetary` in the company currency | **Currency** (8), Currency Type MYR | Symbol / Code / Custom display, decimals, clamp | Currency is fixed per field. See §4.3 |
| `monetary` + `currency_id` (any currency per record) | **No native type.** Number (6) + Relationship to Currencies, or one Currency field per currency [Design] | — | Biggest gap. §2 finding 1 |
| `selection` | **Single-select** (11) | Dropdown / Tiled / Progress bar; colours; scores; option set | Option sets can be shared across sheets and across apps in the organisation |
| state badge / `statusbar` | **Single-select**, view mode **Progress bar**, coloured options | `showtype 2` | Renders a stage line (Draft → Sent → Done) filled in the current option's colour [UI] |
| `boolean` | **Check Item** (36) | Check box / Switch / Yes-No, custom labels | Stored "1" / "0" |
| `date` | **Date** (15) | Precision year / month / day, format, allowed weekdays, start/end limits | `showtype 3` = day |
| `datetime` | **Date & Time** (16) | Hour / HH:MM / HH:MM:SS, 12-hour, time zone: user's or app's (UTC+8) | `showtype 1` = minutes |
| `many2one` | **Relationship**, single row (29, `enumDefault 1`) | Dropdown or popup, title and display fields, selection filter with dynamic values (the Odoo domain), search fields, allow add | Can point to a sheet in another app of the organisation |
| `one2many` | Reverse side of a two-way **Relationship** (29, `enumDefault 2`, tab table) or a **Subform** (34) | Table / tab table / card, add, unlink, delete, sort, summary row | Subform for lines typed inside the parent (order lines) |
| `many2many` | **Relationship**, multiple rows on both sides [Inferred] | As above | Not tested here (§9) |
| `many2many` tags | **Multi-select** (10), coloured options, "Open to add options" | `allowadd 1`, `enumDefault2 1` | Users can type a new tag in the dropdown. Use a relation only when the tag carries data |
| image / binary | **File** (14), File Type Image, limit 1 | View mode, fill/fit, watermark, size limit | Signature (42) for signatures |
| priority stars | **Level** (28), Max 3, star icon | Per-level text, fixed or per-level colours | Odoo priority is 0–3 |
| colour index (`color` int) | **Single-select** with coloured options [Design] | Any hex colour per option | No colour-index type |
| country / state / address | **Region** (24), Global, level Province (State) | `enumDefault 1`, `enumDefault2 2` | Value `MY|MY-10` (ISO-based). Street, street 2, zip and city stay Text |
| phone / mobile | **Telephone**, Mobile type (3), default Malaysia | Country chooser on/off, allowed and common countries | Stored E.164: `+60123456789` [Rec] |
| email | **Email** (5) | No duplicates, mask, encryption | — |
| url / website | **Text** with "Parse links" | `analysislink 1` | **Embed** (45) to show a page inside the form |
| user (`res.users`) | **Members** (26) | Single / multi, scope, Permissions (view / owner / none), default Current user | The permission setting gives record access to the person in the field |
| company (`res.company`) | **Relationship** to a Companies sheet [Design] | — | No native company type. Department (27) is for internal org units |
| barcode | **Text** (scan input on mobile) + **Barcode** (47) display | Code128 or QR, source field | The barcode field only draws the source text |
| sequence (`ir.sequence`) | **Autonumber** (33) | Fixed text, number (digits, start, reset daily / weekly / monthly / yearly), creation date, reference field | Rule order is drag-and-drop |
| hierarchy (`parent_id`) | **Relationship** to the same sheet | — | A self-relation creates a **Parent / Child pair** by itself. **Cascading** (35) picks from a tree in another sheet |
| `related` field | **Foreign Field** (30) | Display only (live) or Store Data (synced, searchable) | Stored mode updates at most 1,000 related rows per change |
| computed sum / count | **Rollup** (37) | Count, sum, average, max, min, earliest / latest, distinct options, filter | A rollup of a Currency field is a plain number |
| computed value | **Formula** (31 number, 38 date [CLI], 53 function) | About 90 functions | Function output text / number / date / date-time / time |
| amount in words | **Uppercase** (25) | Source: Currency or Formula | English words with currency names [Rec] |

## 2. Ten findings that matter most for the Odoo rebuild

1. **Currency is fixed per field.** Currency Type is one of 156 ISO currencies ("MYR-RM Malaysian Ringgit"), chosen in the designer. There is no option to take the currency from another field or from the record, and no exchange rates. The value is stored as a plain number (`1234.50`) [UI] [Raw] [Rec]. The default in this organisation is **HKD**, so every build must set MYR. For Odoo's `monetary` + `currency_id`:
   - amounts always in the company currency (prices, costs, MYR totals) → native Currency MYR;
   - amounts in a document currency → Number + Relationship to Currencies, with a Function formula for display and a Number formula for the MYR equivalent [Design]. One Currency field per currency with show/hide rules is possible but clumsy.
2. **Phone is international and normalised.** The Mobile type stores E.164 (`+60123456789`) and displays it locally (`+60 ▾ 012-345 6789`). Per field: default country code (244 countries; the org default is Hong Kong), country chooser on or off (off = `enumDefault 1`), an allowed-country list (`allowcountries`) and a common-country list. The Landline type has no country handling and stores exactly what was typed [UI] [Raw] [Rec].
3. **Region gives country + state with ISO codes.** Global range + level Province (State) = `enumDefault 1`, `enumDefault 2` → value `{"code":"MY|MY-10","path":…}` [Raw] [Rec]. `enumDefault2` counts differently in the two ranges:
   - **Global:** 1 country, 2 state, 4 all levels (3 city is [Inferred]).
   - **Targeted** (one country, `chooserange "MY"`): 1 state, 2 city.

   The picker lists 249 countries, with 16 common countries first. Malaysia has 16 states, and Selangor's district list shows "Klang" twice. The UI shows English names; the API returns the path in Simplified Chinese.
4. **Options are richer than Odoo selections:**
   - any hex colour per option;
   - a score per option (usable in formulas);
   - "Others" with free text;
   - batch add (up to 1,000);
   - option sets shared across sheets. The Option Set dialog also lists every **app** in the organisation, so sets from another app are offered (not tried);
   - "Open to add options", so users create values while typing.

   The Progress bar view mode is Odoo's statusbar. Single-select can switch type only to Multi-select [UI].
5. **Tags = Multi-select with colours + `allowadd`.** The dropdown offers "Or enter to add a new option directly" and "Select All", and renders coloured pills. There is no parent/child among options, so Odoo's parent tag becomes part of the option name (as BUILD-LOG already decided) [UI] [Raw].
6. **Hierarchy is native through a self-relation.** A Relationship to the same sheet creates a two-way pair by itself: **Parent** (single row, dropdown) and **Child** (multiple rows, tab table) [UI] [Raw]. That is Odoo's `parent_id` / `child_ids`. The **Cascading** field picks a node from a tree, with full path and an option to store the path. But its data source must be a hierarchy view in **another** sheet (its own sheet is not offered), or a new sheet made by "Create Data Source". It was not saved in the probe [UI].
7. **Units are display text, not UoM.** Number has a prefix/suffix unit, decimals, thousand separator, percentage, clamp, a progress-bar input (min–max, step, fixed or range colours) and a stepper input (step) [UI] [Raw]. Unit conversion (Odoo `uom`) stays a relation plus a formula or workflow.
8. **Sequences are native.** Autonumber combines fixed text (for example `SO`), a number (natural, or fixed length with start value and a daily, weekly, monthly or yearly reset), the creation time (YYYYMMDD / YYYYMM / MMDD / YYYY / custom) and a reference field. The rule order is drag-and-drop; the probe gives `0001SO20261123` [UI] [Rec].
9. **Formulas cover most Odoo computes.**
   - **Number mode** (type 31): arithmetic on fields.
   - **Date mode:** duration, add / subtract, time from now, workdays only.
   - **Function mode** (type 53): about 90 functions in 6 groups (§5.1); output text, number, date, date-time or time. Stored as `dataSource {"type":"mdfunction","expression":"CONCAT($<id>$, \"-X\")"}` [Raw].
   - **Rollup:** count, sum, average, max, min, earliest / latest and distinct options over a relation, with a filter.
   - **Foreign Field:** Odoo's `related`.
10. **Members fields carry record permissions.** A Members field has a Permissions setting: Members (view records), Owner (edit and delete) or Null (store only) (`userPermission` 1 = view [Raw]). Its default can be the Current user. That covers Odoo's `user_id` defaults and part of the record rules. Department and Org-roles have the same setting.

Two smaller findings that save rework:
- **Uppercase** is the amount in **English** words with the currency's names: "SAY ONE THOUSAND TWO HUNDRED AND THIRTY-FOUR MALAYSIAN RINGGIT AND FIFTY CENTS ONLY" [Rec]. Useful for invoices.
- **Barcode** draws Code128 or QR from a Text, Email, Phone, Concat, Autonumber or Record ID field, or a QR of the record's own link [UI].

## 3. Settings every field has

Each field's panel has four tabs [UI]:

| Tab | Contents |
|---|---|
| Settings (gear) | Type-specific settings (below), Width (1/4, 1/3, 1/2, 2/3, 3/4, 1), Field Attributes: Read-only, Hide, Hide when adding a record |
| Style (palette) | Field title style and font size (1, 1.2, 1.4, 1.6, 1.8); field value style and size; **Style Rules** |
| Events (lightning) | Control events: when form data meets conditions, show messages or call APIs |
| Description | HintText, Field Description (Auto / Tooltips / Below), **Field Alias**, Remarks |

- **Header:** "View Reference" (where the field is used) and a type switch. Switching was offered as follows [UI]:
  - Text → Email, Telephone, Autonumber, API Query, Rich Text;
  - Number → Currency, Level;
  - Currency → Number;
  - Single-select → Multi-select.
- **Dynamic default value** (icon beside Default Value) [UI]:
  - Number, Currency and Text: Other field values / Query worksheet / Function calculation;
  - Members: Current user / Other field values / Query worksheet.
- **Mask display** opens Mask Settings with these rules [UI]:
  - Fully mask;
  - Name (first and last character shown);
  - Phone number (first 3 and last 4);
  - Email (first 3, then @ and the rest);
  - Currency (fully masked, 5 virtual characters);
  - ID card (last 4);
  - Address (first 4 and last 4);
  - IP address (first segment);
  - Car number (first and last 2);
  - Custom rules.

  Raw key `datamask`.
- **Data encryption** exists on Text, Email and Telephone (`encryid`) [UI] [Raw].
- Every field's `advancedSetting` carries `sorttype` (`en` or `zh`) [Raw].

## 4. Basic fields

### 4.1 Text (type 2)

- **Settings** [UI]:
  - Type: Single Line / Multiple Lines / Markdown.
  - Default value.
  - Validation: Required, No duplicate values, Character limit (min ~ max), Restrict input format. The format dialog offers presets (Letter, Alphanumeric, Number, Capital letters, Lower case, 6 letters, 6-digit number, Postal Code, IP Address, Link) or a custom regular expression with caption, error message and a test box.
  - Advanced: Parse links, Sort by Pinyin.
  - Security: Mask display, Data encryption.
  - Mobile: Allow barcode scanning, Allow QR code scanning.
  - Multiple Lines drops Security. Markdown also drops no-duplicates, the input format and Pinyin sorting.
- **Raw:**
  - `enumDefault` 2 single, 1 multiple, 3 Markdown;
  - `analysislink "1"` = parse links;
  - `filterregex`, `datamask`, `encryid`;
  - `checkrange` + `min`/`max` = character limit;
  - `unique` (top level) = no duplicates.
- **Renders:** a plain input; multiple lines keep line breaks; links become clickable [UI].
- **Odoo:** `char`, `text`, codes (`default_code`, `ref`, `vat`), url.

### 4.2 Number (type 6)

- **Input Method** [UI]:
  - **Number:** decimal places, Omit the trailing 0, Unit (Prefix / Suffix + text), default value, Required, Clamp value (min ~ max), Display thousand separator (on by default), Display as Percentage, Mask.
  - **Progress bar:** Interval min – max (0 – 100), Step Length, Color (Fixed Color / Dynamic: "when the value ≤ N, the colour is …", several ranges), Display input box, Display scale, Display as Percentage.
  - **Pedometer** (stepper): Step Length, decimals, unit, clamp, separator, percentage.
- **Raw:**
  - `advancedSetting.showtype` 0 number, 2 progress bar, 3 stepper;
  - `numinterval` = step;
  - `min`/`max` (+ `checkrange "1"` for the clamp);
  - `suffix` / `prefix` = unit text, for example `suffix "kg"` (the top-level `unit` stays empty);
  - `thousandth "0"` with the separator on ("1" = off [Inferred]);
  - `numshow "1"` = percentage, with `suffix "%"`;
  - `itemcolor` = `{"type":1|2,"color","colors":[{"key":"100","value":"#1677ff"}]}`;
  - `showinput "1"`;
  - `dot` = decimals;
  - `roundtype "2"`.
- **Stored:** 12.5 in a 2-decimal field → `12.50`. **15 % → `0.15`** [Rec].
- **Renders:** `12.50 kg`; the stepper has up/down arrows; percent shows `15%`; the progress bar is a slider with an input box [UI].
- **Limits:** the unit is static text. Number can switch to Currency or Level.
- **Odoo:** integer and float fields, quantities with a fixed unit, percentages (probability, discount), weights, volumes.

### 4.3 Currency (type 8)

- **Settings** [UI]:
  - **Currency Type:** 156 currencies, ISO code + symbol + name, for example "MYR-RM Malaysian Ringgit", "USD-$ US Dollar", "EUR-€ Euro". The org default is HKD.
  - Decimal Places (default 2) + Omit the trailing 0.
  - **View Mode:** Symbol / Code / Custom. Custom has Prefix / Suffix + text, and warns "Duplicate with system type" when the text equals an ISO code.
  - Default Value (fixed, or other field / query / function).
  - Validation: Required, **Clamp amount** (min ~ max).
  - Security: Mask display.
- **Dynamic or per-record currency: none.** The currency list holds only fixed currencies, with nothing like "from field". The dynamic default applies to the **amount** only. Formula and Rollup results are plain numbers. A Rollup of a Currency field shows a free-text unit, not the currency [UI].
- **Raw:**
  - `advancedSetting.currency` = `{"currencycode":"MYR","symbol":"RM"}`;
  - `currencynames` = `{"0":"<Chinese name>","1":"Malaysian Ringgit","2":"Malaysian Ringgit","3":"cents","4":"cent"}`, used for amount in words;
  - **`showformat` "1" Symbol, "2" Code, "0" Custom**, with `prefix` / `suffix` text;
  - `dot` = decimals;
  - `roundtype "2"`;
  - `checkrange` + `min`/`max` = clamp;
  - `enumDefault2 2` on all three probes (meaning not known);
  - top-level `unit` empty.
- **Stored:** `1234.50`, `99.99`, `50.00` [Rec].
- **Renders:** list `RM 1,234.50`; form "RM" + `1,234.50`; Code mode `USD 99.99`; custom prefix `Euro 50.00` [UI].
- **Odoo:**
  - company-currency amounts: `list_price`, `standard_price`, MYR subtotals, `amount_total` when the document is always in MYR;
  - a currency per document: see §2 finding 1.

### 4.4 Email (type 5)

- **Settings:** default value, Required, No duplicate values, Mask display, Data encryption [UI].
- **Stored:** as typed [Rec].
- **Odoo:** `email`, `email_from`.

### 4.5 Date (type 15) and Date & Time (type 16)

- **Settings** [UI]:
  - Type: Date / Date & Time.
  - Date precision: Year / Year-Month / YYYY-MM-DD.
  - Date format: 2026-11-23, 2026/11/23, Chinese, 11/23/2026 (US), 23/11/2026 (EU), Custom.
  - Date & Time adds:
    - Time Format: Hour / HH:MM / HH:MM:SS, plus a 12-hour option;
    - **Time Zone:** Follow current user's timezone / Follow app timezone (UTC+8);
    - Show timezone label.
  - Validation: Specified day only (choose weekdays) and, for date-time, Specified time only.
  - Advanced: Minutes Interval, Start date / End date limits, "Default to start date".
- **Raw:**
  - type 15 / 16;
  - `showtype` "3" day, "1" date-time to the minute ("4" month [Earlier]; the year value was not tested);
  - `showformat "0"`;
  - `allowweek`, `allowtime`;
  - `min` / `max`;
  - `locationbegin`.
- **Stored:** `2026-11-23` [Rec].
- **Trap** [Earlier]: `showtype 4` with a day format shows only the month and breaks Gantt views.
- **Odoo:** `date`, `datetime` (`date_order`, `date_deadline`, `create_date`).

### 4.6 Time (type 46)

- **Settings:** HH:MM / HH:MM:SS, default, Required, Minutes Interval, Start time / End time [UI].
- **Raw:** top-level `unit "1"` for HH:MM; `timeinterval` [Raw].
- **Odoo:** float_time (working hours). Odoo stores hours as a float, so pick per case.

### 4.7 Telephone (type 3 Mobile, type 4 Landline)

- **Mobile settings** [UI]:
  - **Default Phone Code:** 244 countries; the org default is Hong Kong.
  - **Enable selection of country/region** (on by default).
  - **Available countries/regions:** All, or a chosen list (multi-select of 244).
  - **Common countries/regions:** default China, Hong Kong, Taiwan, Macau, Singapore, Malaysia, Japan, South Korea, United States, United Kingdom, France, Germany, Russia. It shrinks to the allowed list when one is set.
  - Default value; Required; No duplicate values; Mask; Data encryption.
  - The Default Phone Code list stays at 244 even when the allowed list is shorter.
- **Landline settings:** none beyond default, Required, No duplicates, Mask, Encryption [UI].
- **Raw:**
  - `defaultarea` = `{"name":"Malaysia","iso2":"my","dialCode":"60"}`;
  - `commcountries` = a JSON list of the same objects;
  - `allowcountries` = the allowed list, present only when restricted;
  - **`enumDefault 1` = country selection switched off.**
  - Type 4 also carries `commcountries` / `defaultarea` (Hong Kong) that the UI never shows [Raw].
- **Stored** [Rec]:
  - Mobile `+60123456789`, and `+60198765432` with the chooser off;
  - Landline `03-1234 5678`, exactly as typed.
- **Renders** [UI]:
  - chooser on: `+60 ▾` + `012-345 6789`. The chooser has common countries first, an A–Z index and "Search by region or area code";
  - chooser off: only the number box, formatted `019-876 5432` on blur;
  - Landline: displayed without the space in the record page.
- **Odoo:** `phone`, `mobile`. Use Mobile type with default Malaysia for both [Design]. Whether a Malaysian landline number is accepted by the Mobile type was not tested.

### 4.8 Region/City (type 24)

- **Settings** [UI]:
  - **Selection Range:**
    - Targeted: one country, from a 202-country list with common countries first;
    - Global: 249 countries.
  - **Scope Level:**
    - Global: All Levels / Country / Province (State) / City (County);
    - Targeted: Province (State) / City (County).
  - **Common countries/regions** (Global): default China, Hong Kong, Taiwan, Macao, Singapore, Japan, United States, Canada, Australia, United Kingdom, Germany, France, South Korea, Malaysia, New Zealand, Russia.
  - Default value, Required.
  - Advanced: **Mandatory full-level selection.**
- **Raw:**

| Setting | Value |
|---|---|
| Global, Country | `enumDefault 1`, `enumDefault2 1` |
| Global, Province (State) | `enumDefault 1`, `enumDefault2 2` (**country + state, confirmed**) |
| Global, City (County) | `enumDefault2 3` [Inferred] |
| Global, All Levels | `enumDefault 1`, `enumDefault2 4` |
| Targeted Malaysia, Province (State) | `enumDefault 0`, `enumDefault2 1`, `chooserange "MY"` |
| Targeted Malaysia, City (County) | `enumDefault 0`, `enumDefault2 2`, `chooserange "MY"` |
| Common countries | `commcountries` `["CN","HK",…]` (ISO2) |
| Mandatory full-level selection ticked | `anylevel "1"`, despite the name |

- **Stored** [Rec]:
  - `{"code":"MY|MY-10|MY-10-28","path":"雪兰莪/乌鲁冷岳县"}` (Selangor / Hulu Langat);
  - `{"code":"MY|MY-10","path":"马来西亚/雪兰莪"}`.

  The codes are ISO-based: MY-10 = Selangor, matching ISO 3166-2 and the MyInvois state codes [Earlier]. **The API path is Simplified Chinese; the UI shows `Selangor/Hulu Langat` and `Malaysia/Selangor`.**
- **Renders:**
  - a cascader: country → state → district, with ▸ on parents;
  - Malaysia lists Johor, Kedah, Kelantan, Kuala Lumpur, Labuan, Melaka, Negeri Sembilan, Pahang, Penang, Perak, Perlis, Putrajaya, Sabah, Sarawak, Selangor, Terengganu;
  - Selangor lists Gombak, Hulu Langat, Hulu Selangor, Klang, **Klang (again)**, Kuala Langat, Kuala Selangor, Petaling, Sabak Bernam, Sepang, Shah Alam.

  Without "Mandatory full-level selection", a user can stop at the state in a city-level field [UI].
- **Limits:**
  - XI (Northern Ireland) and XK (Kosovo) are missing [Earlier];
  - no postcode;
  - names follow the viewer's language [Earlier].
- **Odoo:** `country_id` + `state_id` on partners, companies and banks → one Region field, Global, Province (State). `res.country.state` is not needed [Earlier]. Street, street 2, zip and city stay Text.

### 4.9 Single-select (type 11) and Multi-select (type 10)

- **Single-select view modes** [UI]:
  - **Dropdown list**;
  - **Tiled**: Arrangement Horizontal / Vertical / Matrix, Show all when read-only;
  - **Progress bar**: Mobile Display Horizontal / Vertical; forced to full width.
- **Multi-select view modes** [UI]:
  - **Dropdown list** or **Tiled** (Tiled is the default; Arrangement Horizontal / Vertical / Matrix);
  - Validation: **Limit the number of options** (min ~ max);
  - Advanced: Show select all, Show all when read-only.
- **Options source:**
  - **Custom**, or **Option Set**. The Option Set dialog has an **App** selector listing every app in the organisation (so sets from another app are offered; not tried), an Option Set list and "Create Option Set".
  - This app has no option sets yet; none was created.
- **Colours:**
  - the "Color" toggle gives each option a picker with 27 basic swatches, recent colours and any HEX value;
  - default pastels `#C9E6FC`, `#C3F2F2`, `#C2F1D2`, ….
- **More Actions:** Show others (adds an option "Misc." with free text, key `other`), Sort by Pinyin A-Z / Z-A, Copy all options, Convert to option set.
- **Add Option, Batch Add:** one per line, up to 1,000. Duplicates are ignored; duplicates in the recycle bin are restored.
- **Advanced:**
  - **Assign score values to options:** a dialog with a switch and a score per option, positive or negative. "Field values are the sum of selected item scores" in formulas and defaults.
  - **Open to add options:** not offered in Progress bar mode or in Tiled multi-select.
- **Raw:**
  - `options[]` = `{key (uuid), value, index, isDeleted, color (hex), score, hide}`;
  - **`enumDefault2 1` = colours on; `enumDefault 1` = scores on.** Colours are stored even with the toggle off;
  - `showtype` "0" dropdown, "2" progress bar ("1" tiled [Inferred]). **Correction, 24 Nov [UI]:** on a type 9 Single-select, `showtype` "0" still renders tiles. The designer's View Mode "Dropdown list" changes the field to **type 11** with `showtype` "0" (option keys unchanged; a workflow condition stored with type 9 still matched after the change);
  - **`allowadd "1"`** = open to add. Switching to Progress bar reset it to "0";
  - `otherhint` for the Others option;
  - multi-select: `checktype "1"` in Dropdown mode, `direction`, `showselectall`, `readonlyshowall`, `checkrange` + `min`/`max`;
  - `strDefault "index"`.
- **Stored:** `[{"key":"04e48a56-…","value":"Sent"}]`; for multi, a list of key/value pairs [Rec].
- **Renders** [UI]:
  - dropdown shows coloured pills;
  - the multi dropdown lists "Or enter to add a new option directly" and "Select All", then the options;
  - Progress bar shows the stage line with labels, filled to the current stage in that option's colour.
- **Odoo:**
  - `selection`, `state` (Progress bar for the statusbar);
  - `priority` alternatives;
  - `color` index;
  - tags without data → Multi-select with `allowadd`.

### 4.10 Members (type 26), Department (type 27), Org-roles (type 48)

- **Members** [UI]:
  - Select Method Single / Multi.
  - Selection Range: User address book / Organization Contacts / Scope of designated persons.
  - **Permissions:** Members (View records) / Owner (Edit and delete records) / Null (Only store data).
  - Default: Current user / Other field values / Query worksheet.
  - Required, No duplicate values, Notified when join.
  - The picker shows "Myself" and frequent contacts.
- **Department** [UI]:
  - Single / Multi.
  - Range: All / Designated departments only / Designated and sub-departments / Only sub-departments of the designated.
  - Permissions (default Null); Show dept. path; Show deleted department (on).
- **Org-roles** [UI]: Single / Multi; Range All / Designated Org-roles; Permissions (default Null).
- **Raw:**
  - **`userPermission`** 1 for "Members (View records)" and 0 for "Null" (2 = Owner [Inferred]);
  - Members `usertype "1"`, `checkusertype`, `chooserange`;
  - Department `departrangetype`, `showdelete`.
- **Stored:** `[{accountId, fullname, avatar, …}]` [Rec]. The API readback includes the person's e-mail and mobile.
- **Odoo:** `user_id`, `create_uid`-like owners (Salesperson, Responsible), followers. Departments and roles for HR.

### 4.11 File (type 14)

- **Settings** [UI]:
  - **View Mode:** Thumbnail / Card / List / Poster.
  - Fill Method: Fill / Fit.
  - Display the file name in the cell.
  - **File Type:** Unlimited / Image / File / Audio / Video / Custom.
  - Sort: Latest in front / Oldest in front / Custom.
  - Validation: Required, **Limit the number of files** (default 1), **Limit single file size** (MB), Verify the file name.
  - Operations: Allow upload, Take Photo on PC, Scan to Upload, Allow deletion, Allow downloads (single file / download all).
  - Advanced: Image watermark, Online document editing.
  - Mobile: Take a photo, Record video, Automatically compress images (Mobile App / H5).
- **Raw:**
  - `filetype` `{"type":"1","values":[]}` after choosing Image;
  - `maxcount "1"`, `max` (size);
  - `showtype "1"`, `covertype "0"`;
  - `allowupload` / `allowdelete` / `allowdownload` / `alldownload`;
  - `watermark`, `webcompress`;
  - `enumDefault 3`.
- **Odoo:** `image_1920`, attachments, `binary` documents.

## 5. Advanced fields

### 5.1 Formula (types 31, 38, 53)

- **Formula Mode** [UI]:
  - **Number:** expression with + − × ÷ ( ) and fields; "Treat empty calculation fields as 0"; decimals with round up / down / off; omit trailing 0; unit; thousand separator; percentage.
  - **Date:** Duration between dates / Add or subtract time from a date/time / Time from the moment.
    - Start and End are each a fixed date or a field; the field picker offered Last Modified Time, Creation Time, Date, DateTime and Time.
    - Format of dates without time: 00:00–24:00 or 00:00–00:00.
    - Decimals, Unit (years / months / days / hours / minutes / seconds) with auto-carry, display unit, **Consider workday only**.
  - **Function:** an editor with a field tab and a function list; output format Text / Number / Date / Date & Time / Time.
- **Functions** [UI]:

| Group | Functions |
|---|---|
| Common | IF, CONCAT, AVERAGE, SUM, NETWORKDAY, DATEADD, DATEIF |
| Math | SUM, AVERAGE, MIN, MAX, PRODUCT, COUNTA, ABS, INT, MOD, ROUND, ROUNDUP, ROUNDDOWN, CEILING, FLOOR, POWER, LOG, COUNTBLANK, COUNTARRAY, COUNTCHAR, RANDBETWEEN, NUMBER, PI, RADIANS, DEGREES, SIN, COS, TAN, COT, ASIN, ACOS, ATAN, ACOT, NORM_S_DIST, PERMUT, COMBIN |
| Date | NETWORKDAY, MINUTE, HOUR, WEEKDAY, DAY, MONTH, YEAR, DATEADD, DATEIF, WORKDAY, WORKDAY_INTL, WEEKNUM |
| Text | CONCAT, REPLACE, MID, LEFT, RIGHT, TRIM, CLEAN, REPT, LOWER, UPPER, FIND, FINDA, SPLIT, JOIN, STRING, SUBSTITUTE, STRREVERSE |
| Logical | IF, OR, AND, NOT, ISBLANK, INCLUDE, FALSE, TRUE, IFS |
| Advanced | ENCODEURI, ENCODEURICOMPONENT, DECODEURI, DECODEURICOMPONENT, DISTANCE, GETPOSITION |

  The editor notes: "When using complex fields like options as text, please use the STRING function" [UI].
- **Raw:**
  - Number mode = type 31: `dataSource "2*3"` (fields as `$<controlId>$`), `enumDefault 1`, `strDefault "0"`, `nullzero`.
  - Function mode = **type 53**: `dataSource` `{"type":"mdfunction","expression":"CONCAT($<id>$, \"-X\")","status":1}`, `enumDefault2 2` with output Text.
  - Date mode = type 38 per [CLI]; not saved in the probe.
- **Stored:** `2.00` for `1+1` [Rec]. A note in the panel says sheets over 100K rows do not refresh old rows automatically after a configuration change.
- **Odoo:** `compute` fields: amounts, margins, durations, `display_name`-like text.

### 5.2 Check Item (type 36)

- **Settings** [UI]:
  - View Mode: **Check box** (with a Content text beside it) / **Switch** (Display switch text: on / off labels) / **Yes/No** (two labelled radio options).
  - Default value; Required.
- **Raw:**
  - `showtype` 0 / 1 / 2;
  - `itemnames` `[{"key":"1","value":"On"},{"key":"0","value":"Close"}]`. The English UI defaults the off label to "Close";
  - `defsource` for the default.
- **Stored:** `"1"` / `"0"` [Rec].
- **Odoo:** `boolean` (`active`, `is_company`). Yes/No suits questions; Switch suits flags.

### 5.3 Level (type 28)

- **Settings** [UI]:
  - **Style:** 21 icons: star, smiley, light bulb, sun, thumb up, rocket, fire, heart, bug, warning, emergency, pin-top, flag, bookmark, cross, flower, inbox, snow, shield, rectangle, rounded square.
  - **Max** (default 5).
  - **Color:** Pin (fixed) / Dynamic (one colour per level).
  - Default value; Required.
  - Advanced: Show selected results, **Custom level text** (a description per level, shown on hover or select).
- **Raw:**
  - `max "5"`, `itemicon "star"`;
  - `itemcolor` `{"type":2,"colors":[{"key":"1","value":"#FED156"},…]}`;
  - `itemnames` `[{"key":"1","value":"Low"},…]`;
  - `enumDefault 1`.
- **Stored:** `3`. **Renders** 3 of 5 stars in `#FED156` [Rec] [UI].
- **Odoo:** `priority` (set Max 3), ratings, favourite (Max 1).

### 5.4 Concat (type 32)

- **Settings** [UI]:
  - fields and literal text in one editor;
  - sources include almost every type plus Record ID, Last Modified Time, Creation Time, Creator and Owner;
  - Parse links; Sort by Pinyin.
- **Raw:** `dataSource "$<id>$ - "`.
- **Stored:** `TEST probe - ` [Rec].
- **Odoo:** `display_name`, `complete_name` (one level), reference strings.

### 5.5 Autonumber (type 33)

- **Rules** [UI], drag-ordered:
  - **Number:** Natural Number ID, or Fixed-length with Digits (default 4) and "Numbering continues to increment after exceeding digit limit". Start Value; "Use updated start value for the next record"; Cycle Reset: Do not reset / Daily / Weekly / Monthly / Annually.
  - **Fixed Character.**
  - **Creation Time:** YYYYMMDD / YYYYMM / MMDD / YYYY / Custom.
  - **Reference Field:** Text, Date, Region, Single / Multi-select and Time fields were offered.
  - Advanced: Sort by Pinyin, Displayed in app time zone.
- **Raw:**
  - `strDefault "increase"`;
  - `advancedSetting.increase` = a JSON list of rules:
    - number: `{"type":1,"length":4,"start":"1","repeatType":0}`;
    - fixed: `{"type":2,"controlId":"SO"}`;
    - creation time: `{"type":4,"format":"YYYYMMDD"}`;
    - reference field: type 3 [Inferred];
    - reset values 1–4 [Inferred];
  - `usetimezone "0"`.
- **Stored:** `0001SO20261123`. The probe's order is Number, Fixed, Date, because drag reordering could not be automated [Rec].
- **Odoo:** `name` sequences (SO00001, INV/2026/00001). Put the fixed text first.

### 5.6 Rich Text (type 41)

- **Settings:** Default value, Required [UI].
- **Stored:** HTML, `<p>Rich text probe note.</p>` [Rec].
- **Renders:** a CKEditor box with a toolbar [UI].
- **Odoo:** `html` fields (`description`, `note`, terms).

### 5.7 Positioning (type 40)

- **Settings** [UI]:
  - Input Method: Locate the position on the map / Get current Lat-long.
  - Limit Selection Range: Unlimited / Current surroundings.
  - Display Map, Display Lat-long, Allow custom locations.
- **Raw:** `strDefault "00"`.
- **Odoo:** `partner_latitude` / `partner_longitude`, field-service check-ins.

### 5.8 Signature (type 42)

- **Settings:** Required, Scan to Upload, Allow using the last signature [UI].
- **Raw:** `uselast`, `allowappupload`.
- **Odoo:** `signature` on orders and deliveries.

### 5.9 OCR (type 43)

- **Settings** [UI]:
  - Interface Service: Default (built-in; "credits will be deducted automatically") / Integration.
  - Recognition Template: General text / Chinese ID card / VAT Invoice.
  - Map to current record / subform details; Field Mapping; Mobile: Disable album.
- **Raw:** `ocrmap "[]"`, `enumDefault 1`. Saved without a mapping, the field shows a red "No mapping fields configured" warning [UI].
- **Odoo:** document digitisation (Enterprise). Credits apply.

### 5.10 API Query (type 49 in Button mode)

- **Settings** [UI]:
  - View Mode: Button / Dropdown list / Searchable Dropdown List.
  - Call Source: Integrated API / PBP.
  - The API is picked from the organisation's Integration Center.
  - Write returned data into form fields.
- **Raw:** saved as **type 49**, which the [CLI] calls "Button"; it calls 50 "APIQuery". The dropdown modes are probably 50 [Inferred].
- **Odoo:** VAT / company lookups, live rates. Needs an integration, so not native data.

### 5.11 Barcode (type 47)

- **Settings** [UI]:
  - **Barcode:** Code128; numbers, letters and symbols, up to 128 characters. Data Source: Record ID, Text, Email, Telephone, Concat or Autonumber. Number fields are not offered.
  - **QR Code:** supports Chinese, up to 250 characters. Data Source "Record internal link" or "Field Value"; Fault Tolerance 7 / 15 / 25 / 30 %.
  - Max Width (px).
- **Raw:**
  - `enumDefault` 1 barcode / 2 QR;
  - `dataSource "$<field>$"`;
  - QR from the record link: `enumDefault2 1`, `faultrate "30%"`;
  - `width "160"`.
- **Stored:** the source text `SKU-0001`; empty for the record-link QR [Rec].
- **Renders:** a barcode and a QR image, live in the form [UI].
- **Odoo:** `barcode` on products and lots (display and labels). Data entry stays a Text field with mobile scanning.

### 5.12 Uppercase (type 25)

- **Settings:** Associated Amount, from a Currency or Formula field [UI].
- **Raw:** `dataSource "$<currency field>$"`, `currencytype "1"`.
- **Stored:** "SAY ONE THOUSAND TWO HUNDRED AND THIRTY-FOUR MALAYSIAN RINGGIT AND FIFTY CENTS ONLY" [Rec]. The unsaved form preview showed "… HUNDRED THIRTY FOUR …" (§8).
- **Odoo:** amount in words on invoices and cheques (`amount_to_text`).

### 5.13 Embed (type 45)

- **Type** [UI]:
  - **Stats:** a chart from the app, with "Filter Chart";
  - **View:** a worksheet view with "Filter View" and "Show Add button";
  - **Link:** a URL that can contain field values; "Enable opening new page".
  - Max Height (px).
- **Raw:** Link = `enumDefault 1`, `dataSource "https://www.nocoly.com"`, `height "400"`.
- **Renders:** an iframe in the form [UI].
- **Odoo:** smart-button-like related lists (View + filter), dashboards in forms, external pages.

### 5.14 Custom Field

- **Creation dialog** [UI]:
  - "Store field value" (usable for search, filter, export), with Storage Type Text / Number / Date / Time / Single-select / Multi-select / Relationship;
  - or "Only reference other field values".
- **Panel:** Store data as …, **Enter AI-powered Dev**, Reference Field list with `env.*` variable names, Default Height 240 px, plus the storage type's own settings.
- **Raw:** a stored Text custom field is **type 2** with `customtype "1"`, `freeid` (widget id), `height "240"`, `allowfull "1"`. The [CLI] lists 54 "CustomField", probably the reference-only mode [Inferred].
- **Use:** presentation only (`../README.md` §3, principle 5: up to 5 per sheet). Business rules stay in native fields.

## 6. Relational fields

### 6.1 Relationship (type 29)

- **Creation dialog** [UI]:
  - "New association" / "Create two-way link";
  - **App:** this app, or another app in the organisation;
  - Related Worksheet.
- **Self-relation** [UI] [Raw]: a relation to the same sheet is created as **Parent** (single row) and **Child** (multiple rows, tab table) with "Link Method: Two-way Link".
- **Panel** [UI]:
  - Relationship Quantity: Single row / Multiple rows.
  - View Mode: single = Dropdown list / Popup; multiple = Card / Dropdown list / Table / Tab table.
  - Title Field; Display Fields.
  - **Related Record Settings:**
    - *Selection Limit*: filters with dynamic values (Odoo `domain`);
    - *Dropdown Settings*: extended mode with extra fields and cover, and a popup selection table with filters;
    - *User Query*: search all text fields or chosen fields, show records only after a search, filter fields in the popup.
  - Sort (multiple): Allow drag sorting, by adding time / set order / linked view.
  - Default value; Required; No duplicate values.
  - Operation Settings: Select existing records (All / Viewable), Add records, Unlink records, Delete records, Allow import and add, Allow opening records (+ View), Allow export, Allow batch operations, Show the record shortcut.
  - Advanced: Link View, Filter the displayed results, Show count, Show summary row.
  - Mobile: Scan to add association.
- **Raw:**
  - `enumDefault` 1 single / 2 multiple;
  - `dataSource` = target worksheet id; `sourceControlId` = the paired field;
  - `showtype` "3" dropdown, "6" tab table;
  - `allowlink`, `searchrange`, `scanlink`, `scancontrol`, `allowdelete`, `allowedit`, `allowexport`, `showquick`, `choosetype`, `allowcancel`, `sorts`, `choosesorts`;
  - `strDefault "000"`.
- **Odoo:** `many2one`, `one2many` (the reverse side), `many2many` (both sides multiple, §9), `parent_id` / `child_ids`.

### 6.2 Query Records (type 51)

- **Creation** [UI]:
  - "Create Query" / "Existing association"; App;
  - Query Sheet: **Worksheet** or **Aggregated Table**;
  - if a relation exists, it offers "query the association";
  - Query conditions: field + operator (is / is one of / not any of / is empty / is not empty, for an option field) + a value-source select showing "Fixed Value" (its other choices did not open; a dynamic value is [Inferred]);
  - Sort (default Creation Time, earliest first).
- **Display:**
  - Single Record or Multiple Records, with View Mode Card / Text / Table / Tab table, Display Field, Query Quantity;
  - Add records, Allow opening records, View, Allow export;
  - Advanced: Show by user permissions, Show summary row.
- **Raw:**
  - `enumDefault 2` (multiple), `dataSource` = sheet;
  - `resultfilters` (JSON filter, option values by key), `sorts` `[{"controlId":"ctime","isAsc":true}]`;
  - `showtype "5"` (table), `querytype "0"`.
- **Stored:** nothing; it is computed on display. It showed "Total 0 row(s)" [Rec] [UI].
- **Odoo:** smart buttons and related lists that are not a foreign key (other orders of the same customer).

### 6.3 Subform (type 34)

- **Creation** [UI]: **Add from blank** (creates a new child sheet; not used here) / **Use an existing sheet** (any sheet in this or another app).
- **Panel** [UI]:
  - Display Field.
  - Validation: Required, Limit rows added, Duplicate inputs not allowed globally, Duplicate entries not allowed in this record (fields).
  - Sort: by set order / Drag to Sort.
  - Operations: Add new items (Add row, Add associated record fields, Import new, Copy), Edit existing, Delete existing, Allow popup opening, Allow batch operations, Allow export.
  - Advanced: Show count, Show summary row, Access by user permissions, Show hidden fields.
  - Mobile: Display Style List / Card / Table; up to 3 summary fields.
- **Raw:**
  - `enumDefault 2`, `dataSource` = sheet;
  - `sourceControlId` = a hidden reverse field, not listed by `worksheet fields`;
  - `max "200"`, `min "0"`, `enablelimit "0"`, `rownum "15"`, `blankrow "1"`, `showtype "1"`;
  - `uniquecontrols`, `controlssorts`, `detailworksheettype "1"`;
  - allow* switches.
- **Renders:** a grid with "Add a row" [UI].
- **Odoo:** `order_line`, `invoice_line_ids`, `move_ids`: lines entered with the parent.

### 6.4 Cascading (type 35 [CLI])

- **Data source** [UI]: "Select a hierarchical view as the data source … Only supports the table's own hierarchical structure":
  - **Create Data Source** creates a new sheet;
  - **Select an existing worksheet** + **Hierarchy View**. The probe sheet itself was **not** offered, and no other sheet here has a hierarchy view.
- **Panel** [UI]:
  - Select Method Single / Multi; Dropdown Style **Cascading menu / Tree selection**;
  - Filter Data Sources All / Viewable;
  - Selection Range Start (Top-level nodes) – End (Final layer); Select Method (Arbitrary choice, …); Number of selected levels backwards;
  - **Show full path of selection**, **Store hierarchy path**, Search settings.
- **Not saved:** a new data-source sheet would change more than the probe.
- **Odoo:** pickers for `product.category`, `stock.location`, `account.group` once those sheets have a self-relation and a hierarchy view [Design].

### 6.5 Foreign Field (type 30)

- **Settings** [UI]:
  - Related Records: only the single-row relation "Parent" was offered;
  - Display Field: any field of the related sheet, plus Owner, Creator, Creation Time, Last Modified Time;
  - **Type:**
    - **Display Only**: "real-time data fetch on record load";
    - **Store Data**: "store data in the current table and keep it synced; usable for search, filter, sort, stats, or in formulas. Stored data may lag; when the source changes, up to 1,000 related rows are updated".
- **Raw:** `dataSource "$<relation id>$"`, `sourceControlId` = the source field, `sourceControlType`, **`strDefault "00"` = Store Data** ("10" = display only [Earlier]).
- **Odoo:** `related=` fields (`partner_id.country_id`, `product_id.uom_id`).

### 6.6 Rollup (type 37)

- **Settings** [UI]:
  - Related Records: only the multiple-row relation "Child" was offered.
  - Rollup: Number of Records, or a field.
  - Aggregations by field type:

| Field type | Aggregations |
|---|---|
| Number / Currency | Filled Count, Unfilled Count, Deduplicate, Sum, Average, Max, Min |
| Date | Filled Count, Unfilled Count, Deduplicate, Latest, Earliest |
| Options | Filled Count, Unfilled Count, Deduplicate, Count distinct options |

  - Summary Range filter; decimals with rounding; Unit prefix/suffix; thousand separator.
- **Raw:**
  - `dataSource "$<relation id>$"`, `sourceControlId` = the field;
  - **`enumDefault` 5 = Sum, 6 = Number of Records**; `enumDefault2 6`.
- **Stored:** `0` with no children [UI].
- **Limits:** the result is a number. A Currency source does not carry its symbol; set a unit text.
- **Odoo:** `amount_untaxed` (sum of lines), counts on smart buttons.

### 6.7 Free Link (type 21)

- **Settings:** Type All / Task / Project / Calendar / Application Form [UI]. It links Mingdao collaboration objects.
- **Odoo:** no direct use. Possibly calendar links [Design].

## 7. Layout

| Field | Settings [UI] | Raw |
|---|---|---|
| **Section** (22) | Style: text colour, theme colour; Default Status Expand / Collapse / Non-collapsible | `theme "#1677ff"`, `color`, `enumDefault2 1` |
| **Tabs** (52) | Added with a "Tab position" choice: Top / Bottom / Left. Field Name, Icon, Read-only, Hide. Multi-row relations, subforms and query records sit in a Tabs area (Tiled / Collapsed) | type 52, which the [CLI] calls "Section" |
| **Remarks** (10010) | Static rich-text guidance on the form; the field name is hidden by default | `dataSource` = HTML, `hidetitle "1"`; `sectionId` = the tab it sits in |

## 8. Differences between the UI and the CLI readback

1. **Region path language.** The UI shows `Selangor/Hulu Langat` and `Malaysia/Selangor`. The CLI returns `雪兰莪/乌鲁冷岳县` and `马来西亚/雪兰莪`. The `code` (`MY|MY-10|MY-10-28`) is the stable value to build on.
2. **Amount in words.** The unsaved form preview read "… TWO HUNDRED THIRTY FOUR …". The stored value reads "… TWO HUNDRED AND THIRTY-FOUR …". Client and server word it differently.
3. **Percent and phone formats.** The UI shows `15%` and stores `0.15`. The UI shows `012-345 6789` and stores `+60123456789`. The landline was stored as typed (`03-1234 5678`); the record page showed `03-12345678`.
4. **Type numbers versus CLI names.**

| Palette name | Stored as | CLI name for that number |
|---|---|---|
| API Query (Button mode) | 49 | Button (50 is "APIQuery") |
| Tabs | 52 | Section |
| Section | 22 | Divider |
| Free Link | 21 | DynamicLink |
| Custom Field (stored as Text) | 2 + `customtype` | 54 CustomField |
| Single-select, every view mode | 11 | Dropdown (9, FlatMenu, not produced) |
| Region | 24 | 19 / 23 / 24 |
| Function formula | 53 | — (Number mode is 31) |

5. **Hidden fields.**
   - The Subform's reverse field (`<id>`) is referenced by `sourceControlId` but not listed by `worksheet fields`.
   - Type 4 Landline stores `commcountries` / `defaultarea` (Hong Kong) that its panel never shows.
   - Single-select options keep colours when the Color toggle is off.
6. **Setting names versus keys.**
   - "Mandatory full-level selection" is stored as `anylevel "1"`.
   - Switching a Single-select to Progress bar silently reset `allowadd` from on to "0".
   - Currency has `enumDefault2 2`, meaning unknown.
7. **Automation traps met while probing.** These are UI facts, not product bugs:
   - A CodeMirror value set through the editor's API did not persist for the Embed link (real typing did). It did persist in the function editor, which reads the value on Save. Concat and Number-formula expressions were typed.
   - Pressing Escape in the new-record form starts "Save the filled content as a draft?". Its × keeps the form open.
   - Several pickers toggle: a second click closes them.

## 9. Not tested, or still open

- Many-to-many: a two-way relation with **both** sides "Multiple rows". Only the single ↔ multiple self-pair was built.
- Cascading end to end. It needs a tree sheet with a self-relation and a hierarchy view, for example the future Product Categories.
- Date-mode formula (type 38) saved and read back; API Query dropdown modes (type 50?); OCR mapping.
- Option sets: none created. Cross-app use was only seen in the dialog.
- Members for external portal users (`usertype`), Members multi, and the raw value of the "Owner" permission.
- A Malaysian landline number typed into a Mobile-type Telephone field.
- Region global level 3 (`enumDefault2 3`); the year and month precision values of `showtype`; thousand separator off (`thousandth "1"`?); `filetype` values for types other than Image.
- Whether a kanban view can colour cards by a Single-select. Not checked.

## 10. Raw shapes for CLI builds

These shapes come from the readback after saving in the UI, trimmed to the keys that matter. Values marked "adjusted" were changed for the Odoo case. **Writing them through `app-editor field.add` or `worksheet add-fields` was not tested in this survey.** Add one field, read it back with `worksheet fields --raw`, then repeat. `field.add` can time out although the field was created: read back before retrying [Earlier].

```jsonc
// Currency, MYR, symbol
{"type":8,"dot":2,"advancedSetting":{"currency":"{\"currencycode\":\"MYR\",\"symbol\":\"RM\"}","showformat":"1","roundtype":"2"}}
// Telephone, mobile, default Malaysia, chooser limited to MY + SG
{"type":3,"advancedSetting":{"defaultarea":"{\"name\":\"Malaysia\",\"iso2\":\"my\",\"dialCode\":\"60\"}","allowcountries":"[{\"name\":\"Malaysia\",\"iso2\":\"my\",\"dialCode\":\"60\"},{\"name\":\"Singapore\",\"iso2\":\"sg\",\"dialCode\":\"65\"}]"}}
// Telephone, mobile, Malaysia only, no chooser
{"type":3,"enumDefault":1,"advancedSetting":{"defaultarea":"{\"name\":\"Malaysia\",\"iso2\":\"my\",\"dialCode\":\"60\"}"}}
// Region, country + state, worldwide
{"type":24,"enumDefault":1,"enumDefault2":2}
// Region, Malaysian state only (targeted)
{"type":24,"enumDefault":0,"enumDefault2":1,"advancedSetting":{"chooserange":"MY"}}
// Single-select shown as a status bar, coloured
{"type":11,"enumDefault2":1,"options":[{"key":"<uuid>","value":"Draft","index":1,"color":"#C9E6FC"}],"advancedSetting":{"showtype":"2"}}
// Multi-select tags, coloured, users may add
{"type":10,"enumDefault2":1,"advancedSetting":{"checktype":"1","allowadd":"1"}}
// Number with a unit
{"type":6,"dot":2,"advancedSetting":{"showtype":"0","suffix":"kg"}}
// Level, 3 stars (adjusted: the probe has max 5)
{"type":28,"advancedSetting":{"max":"3","itemicon":"star"}}
// Check item as a switch
{"type":36,"advancedSetting":{"showtype":"1"}}
// Autonumber SO + 5 digits, no reset (adjusted: the probe has Number, SO, date with 4 digits)
{"type":33,"strDefault":"increase","advancedSetting":{"increase":"[{\"type\":2,\"controlId\":\"SO\"},{\"type\":1,\"length\":5,\"start\":\"1\",\"repeatType\":0}]"}}
// Barcode (Code128) from a text field
{"type":47,"enumDefault":1,"dataSource":"$<text field id>$","advancedSetting":{"width":"160"}}
// Function formula, text output
{"type":53,"enumDefault2":2,"dataSource":"{\"type\":\"mdfunction\",\"expression\":\"CONCAT($<id>$, \\\"-X\\\")\",\"status\":1}"}
```

## 11. Probe sheet inventory

Native Field Probe `<id>`, read back at 15:20 MYT. Text in brackets describes the probe; it is not part of the field name.

| Field | type | enumDefault / enumDefault2 | controlId |
|---|---:|---|---|
| Name | 2 | 2 / 0 | `<id>` |
| Currency (MYR, symbol) | 8 | 0 / 2 | `<id>` |
| Text single | 2 | 2 / 0 | `<id>` |
| Text multi | 2 | 1 / 0 | `<id>` |
| Text markdown | 2 | 3 / 0 | `<id>` |
| Number kg | 6 | 0 / 0 | `<id>` |
| Number progress | 6 | 0 / 0 | `<id>` |
| Number stepper | 6 | 0 / 0 | `<id>` |
| Number percent | 6 | 0 / 0 | `<id>` |
| Email | 5 | 0 / 0 | `<id>` |
| Date | 15 | 0 / 0 | `<id>` |
| DateTime | 16 | 0 / 0 | `<id>` |
| Telephone mobile | 3 | 0 / 0 | `<id>` |
| Telephone landline | 4 | 0 / 0 | `<id>` |
| Region MY (targeted, city) | 24 | 0 / 2 | `<id>` |
| Region global (all levels) | 24 | 1 / 4 | `<id>` |
| Region country+state | 24 | 1 / 2 | `<id>` |
| Region country | 24 | 1 / 1 | `<id>` |
| Single-select status (progress bar, colours, scores) | 11 | 1 / 1 | `<id>` |
| Single-select dropdown (open to add, Others) | 11 | 0 / 0 | `<id>` |
| Multi-select tags (colours, open to add) | 10 | 0 / 1 | `<id>` |
| Members | 26 | 0 / 0 | `<id>` |
| Department | 27 | 0 / 0 | `<id>` |
| File image | 14 | 3 / 0 | `<id>` |
| Formula (`1+1`) | 31 | 1 / 0 | `<id>` |
| Check Item | 36 | 0 / 0 | `<id>` |
| Level | 28 | 1 / 0 | `<id>` |
| Check switch | 36 | 0 / 0 | `<id>` |
| Concat | 32 | 0 / 0 | `<id>` |
| Rich Text | 41 | 0 / 0 | `<id>` |
| Positioning | 40 | 0 / 0 | `<id>` |
| Signature | 42 | 0 / 0 | `<id>` |
| OCR (no mapping) | 43 | 1 / 0 | `<id>` |
| API Query (no API chosen) | 49 | 0 / 0 | `<id>` |
| Barcode | 47 | 1 / 0 | `<id>` |
| Uppercase | 25 | 0 / 0 | `<id>` |
| Barcode QR | 47 | 2 / 1 | `<id>` |
| Custom Field (stored Text) | 2 | 2 / 0 | `<id>` |
| Parent (self-relation) | 29 | 1 / 0 | `<id>` |
| Foreign parent region (stored) | 30 | 1 / 0 | `<id>` |
| Rollup child sum | 37 | 5 / 6 | `<id>` |
| Rollup child count | 37 | 6 / 6 | `<id>` |
| Embed (link) | 45 | 1 / 0 | `<id>` |
| Autonumber | 33 | 0 / 0 | `<id>` |
| Check yes/no | 36 | 0 / 0 | `<id>` |
| Org-roles | 48 | 0 / 0 | `<id>` |
| Time | 46 | 0 / 0 | `<id>` |
| Query drafts | 51 | 2 / 1 | `<id>` |
| Subform lines (existing sheet: itself) | 34 | 2 / 0 | `<id>` |
| Free Link | 21 | 0 / 0 | `<id>` |
| Currency USD code | 8 | 0 / 2 | `<id>` |
| Currency EUR custom | 8 | 0 / 2 | `<id>` |
| Region MY state (mandatory full level) | 24 | 0 / 1 | `<id>` |
| Telephone MY fixed | 3 | 1 / 0 | `<id>` |
| Telephone MY fixed 2 (accidental duplicate, renamed) | 3 | 1 / 0 | `<id>` |
| Telephone MY+SG | 3 | 0 / 0 | `<id>` |
| Formula function | 53 | 0 / 2 | `<id>` |
| Formula number 2 (`2*3`) | 31 | 1 / 0 | `<id>` |
| Section | 22 | 0 / 1 | `<id>` |
| Child (reverse of Parent) | 29 | 2 / 0 | `<id>` |
| Tabs | 52 | 0 / 0 | `<id>` |
| Remarks | 10010 | 0 / 0 | `<id>` |

The probe sheet was deleted at the restart on 23 Nov 2026 (15:49) and is in the app recycle bin; the ids above are for reference only.

## 12. Confirmed while building wave 0

Live results from the real sheets (Companies, Bank Accounts, Contacts), 23 Nov 2026. [Rec] = readback, [UI] = checked in the form.

- **Foreign Field, display only** (type 30, `strDefault "10"`, `dataSource "$<relation id>$"`, `sourceControlId`, `sourceControlType`) can be added with `worksheet add-fields`. It works for Region (24), Text (2), Email (5), Phone (3) sources [Rec] [UI]. Two quirks: `record get` returns the Region value as a JSON *string* (P18), and the form shows a Phone source unformatted, "+60123456789" (P19).
- **Function formula in a unique index.** The index dialog offers a type 53 field. A composite unique index on a formula plus a relation is enforced on API writes (resultCode 11) and in the new-record form ("Duplicates are not allowed", shown under the formula's source field) [UI].
- **Function formula recomputes on form edits.** `UPPER(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE($id$," ",""),"-",""),".",""),"/",""))` turned "5140.1234/5678 xy" into "514012345678XY" after Save [UI]. There is no regex function; strip characters one by one.
- **Hidden field:** `fieldPermission "011"` (visible / editable / shown on create). `worksheet fields` then reports `isHidden` and `isHiddenOnCreate` true; the field is absent from the record and new-record forms [UI]. It can be sent in `add-fields --controls`.
- **Image-only attachment:** `advancedSetting.filetype '{"type":"1","values":[]}'` is accepted by `worksheet create --fields` [Rec].
- **Two-way relation to another sheet** through `worksheet create --fields` with `config.bidirectional` creates the reverse field (unlike a self-relation through `add-fields`, P17). Its display columns still have to be set (P5) [Rec] [UI].
- **Form layout** [UI], 24 Nov: each control has `row`, `col` and `size` on a 12-column grid (3 = four per row, 4 = three, 6 = two, 12 = full). A field added later lands at row 9999 with size 0. Fields hidden by a rule or on create leave no gap: the rest of the row moves left. Divider (分段) = type 22 with a title; tabs = type 52 (not used yet). Relation lists shown as tabs (`showtype` "6") render in the tab bar at the bottom wherever their row is. The whole layout is written in one go with `worksheet update-fields --controls @file` (the raw controls as read, only row / col / size changed); `--check` also lists what is already wrong on the sheet (for example "dangling source field" on one-way relations), so compare its "proposed" list with "current".
- **`fieldPermission` third digit = shown on the new-record form.** "101" read-only and shown on create, "100" read-only and hidden on create, "110" editable but hidden on create. A custom-button dialog edits the existing record, so "110" fields still appear in it [UI].
