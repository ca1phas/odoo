# Platform issues found while building (for product tickets)

Started 23 Nov 2026 at the Module Owner's request: record every difference between CLI/MCP and the UI, and anything that behaves like a bug, so it can be raised with the product team. Platform: Nocoly SaaS (www.nocoly.com), organisation on Professional, hap-cli 0.9.14, test app "Odoo Replica (AI)".

**How to use:**
- Each "P" item has ticket-ready fields in Simplified Chinese (labelled fields, 3W, steps, expected vs actual, impact), the format our Mingdao tickets use.
- "D" items are documentation errors, with sources.
- Status: **Open** = not filed. The Module Owner decides what to file and the Platform Liaison files it (roles: `HANDOVER.md` §2); nothing is submitted without approval.

| # | Area | Kind | Severity | Status |
|---|---|---|---|---|
| P1 | Unique index error message | Wrong ids in the message | Low | Open |
| P2 | Region field, CLI create | Hidden default differs from the UI | Low | Open |
| P3 | Region value through the API | Language does not follow the user | Medium | Open |
| P4 | Region field type numbers | CLI type table and server disagree | Low | Open |
| P5 | Multi-relation display fields | Created with no visible columns | Medium | Open |
| P6 | Multi-relation cells in record list / get | Truncated to 5 rows without notice; shapes differ | Medium | Open |
| P7 | Option set with no options | Refused with an empty error | Low | Open |
| P8 | Role create with per-sheet scope on an empty app | Refused with an empty error | Low | Open |
| P9 | CLI options | Inconsistent between commands | Low | Open |
| P10 | `field.add` timeout | Reports failure, but the field is created | Medium | Open (known since 20 Nov) |
| P11 | Amount in words (Uppercase) | Preview differs from the stored value | Low | Open |
| P12 | Field type numbers vs CLI names | Several mismatches | Low | Open |
| P13 | Subform reverse field | Not listed by `worksheet fields` | Low | Open |
| P14 | Landline field | Stores Hong Kong keys the panel never shows | Low | Open |
| P15 | Option colours | Saved while the colour switch is off | Low | Open |
| P16 | Single-select → Progress bar | Silently turns off "allow adding options" | Medium | Open |
| P17 | Self-relation through add-fields | Two-way flag set, but no reverse field created | Medium | Open |
| P18 | Foreign field of a Region field, record get | Returned as a JSON string, the source as an object | Low | Open |
| P19 | Foreign field of a Phone field, record form | Shows the raw stored number, not the formatted one | Low | Open |
| P20 | Hidden fields in `record list` | Returned empty; `record get` returns the values | Medium | Open |
| P21 | CLI workflow DSL, date calculation result | Referenced as string_fx_id; the server uses date_fx_id, so conditions break | Medium | Open |
| P22 | CLI workflow DSL, relation conditions | "Is not empty" cannot be written; raw ids refused | Medium | Open |
| P23 | CLI batch-add, branch paths | A path with a condition loses its name | Low | Open |
| P24 | Region value in workflow functions | Returned as a Chinese path, not the code or the user's language | Medium | Open |
| P25 | CLI workflow DSL, function calculation | Created with 0 decimals: numeric results are rounded to integers | High | Open |
| P26 | Unique index and the recycle bin | A deleted record still blocks its unique values | Medium | Open |
| P27 | CLI workflow DSL, clearing a field | "op: clear" is dropped or refused; the stored form needs isClear | Medium | Open |
| P28 | CLI workflow DSL, rollup of a fetched set | aggregate "sum" is not kept; the node only counts | Medium | Open |
| P29 | Workflow function calculation | A formula error gives an empty result; the run shows success | High | Open |
| P30 | Workflow publish | A step that reads a node inside a branch is refused with an unspecific message | Low | Open |
| P31 | CLI role set-permissions | Changing the level turns every app-wide switch off | High | Open |
| P32 | CLI workflow DSL, fill-in node | A wrongly shaped form-field list gives HTTP 500 instead of a message | Low | Open |
| P33 | Workflow query node | An empty dynamic filter value fails the whole run; build and publish give no warning | Medium | Open |
| P34 | CLI record create | Refused by a "hide" rule because a hidden field has a default value; the same record saves in the UI | Low | Open |
| P35 | CLI record update, option fields | An option text that is not in the list is stored as a dangling key; the form shows an empty tag | Medium | Open |
| P36 | CLI role set-permissions -P | Per-sheet rules are not saved, the command reports success | High | Open |
| P37 | CLI role create-fine | The role is created with every app-wide switch off; a sheet with read scope 0 falls back to "own, everything allowed" | High | Open |
| P38 | CLI create-custom-action, createRelatedRecord | The button shows but does nothing: target saved as "related record" with no relation, and no "Active Button" choice | High | Open |
| D1–D12 | Help docs | Conflicts and outdated content | — | Open |

---

### P1 唯一索引报错信息中的 ID 不是冲突记录

- **谁 / 何时 / 做什么：** Odoo 复刻项目的 Builder，2026-11-23，在 Nocoly SaaS 的测试应用中，通过 hap-cli 写入重复值，测试唯一索引。
- **复现步骤：**
  1. 在 Countries 表的 Country Code 字段上建立唯一索引（表单设置 › 搜索加速 › 新建索引 › 勾选唯一索引）。
  2. 用 `hap worksheet record create` 新增一条 Country Code = MY 的记录（MY 已存在）。
- **预期结果：** 被拒绝，并指出冲突的字段名称和已有记录。
- **实际结果：** 正确拒绝（resultCode 11），但提示 "another record already has them: <id>"。这个 ID 是 Country Code **字段**的 ID，不是已有记录的 ID。组合索引会列出两个字段 ID。
- **影响：** 排查重复数据时会被误导，以为是记录 ID。
- **证据：** `00-foundation-build/BUILD-LOG.md`（23 Nov 唯一索引测试）。

### P2 CLI 创建"国际"范围的地区字段时，服务器自动写入 chooserange = "CN"

- **谁 / 何时 / 做什么：** 2026-11-23，用 `worksheet create --fields` 创建地区字段（type 24，enumDefault 1 = 国际，enumDefault2 1 = 国家）。
- **复现步骤：**
  1. 用 CLI 创建上述字段。
  2. `hap worksheet fields --raw` 读回。
- **预期结果：** 与界面保存的"国际"字段一致，即 `chooserange: ""`。
- **实际结果：** 读回为 `chooserange: "CN"`。在界面中选择"国际"保存的字段则为 `""`。
- **影响：** 两种方式建出的同一设置，存储值不同。目前界面显示正常，但行为是否一致不明，需要手动清空。
- **证据：** BUILD-LOG（Countries 的 Region 字段）。

### P3 API 读取的地区路径语言不随用户语言

- **谁 / 何时 / 做什么：** 2026-11-23，读取 Countries 记录中的地区字段。
- **复现步骤：**
  1. 账户界面语言为英文。
  2. 打开记录：地区显示 "Malaysia"。
  3. 用 `hap worksheet record list` 读取同一字段。
- **预期结果：** path 与用户语言一致（Malaysia）。
- **实际结果：** API 返回 `{"code":"MY","path":"马来西亚"}`（简体中文）。同一天字段调查中，CLI 返回的县市路径也是简体中文，而界面显示英文。
- **影响：** 用 API 或 MCP 生成报表、打印文本或对外接口时，地名语言错误。海外客户（马来西亚）尤其明显。

### P4 地区字段类型编号与 CLI 类型表不一致

- **谁 / 何时 / 做什么：** 2026-11-23，`worksheet add-fields` 以 type 19（省）创建地区字段。
- **复现步骤：**
  1. 用 add-fields 以 type 19 新增地区字段。
  2. 读回。
- **预期结果：** type 19，或者 CLI 说明只使用 24 加层级。
- **实际结果：** 存为 type 24，enumDefault2 = 1。`hap worksheet field-types` 仍列出 19/23/24。
- **影响：** 按文档或 CLI 表写的脚本，读回比对会失败。

### P5 用 CLI 创建的多条关联字段没有显示字段，标签页表格显示 "No visible fields"

- **谁 / 何时 / 做什么：** 2026-11-23，`worksheet create --fields` 创建双向多条关联（Country Groups › Countries，displayMode tabTable，未传 showFields）。
- **复现步骤：**
  1. 用 CLI 创建上述字段。
  2. 打开一条 Country Group 记录。
- **预期结果：** 与界面新建关联一样，默认显示目标表的前几个字段。
- **实际结果：** showControls = []，标签页显示 27 行，但每行都是 "No visible fields"。系统自动生成的反向字段则默认带两个显示字段。
- **影响：** 用户看得到行，却看不出是哪些记录。必须再用 field.update 设置 showControls。

### P6 record list 的多条关联只返回前 5 条，且与 record get 的格式不同

- **谁 / 何时 / 做什么：** 2026-11-23，读回 Country Groups（欧盟有 27 个国家）。
- **复现步骤：**
  1. `hap worksheet record list` 读取多条关联字段。
  2. `hap worksheet record get` 读取同一记录。
- **预期结果：** 返回完整列表，或明确给出总数和截断标记，两个命令格式一致。
- **实际结果：** list 只返回 5 条关联记录，没有提示；get 返回一个整数（27），不是列表。
- **影响：** 校验数据时容易误判为导入缺失。我们一度以为每组只存了 5 个国家。

### P7 新建空的选项集被拒，错误信息为空

- **谁 / 何时 / 做什么：** 2026-11-23，`hap app optionset create --options-json '[]'`。
- **预期结果：** 允许先建空选项集，或者提示"至少需要一个选项"。
- **实际结果：** "The server refused the request (error None)"。
- **影响：** 需要反复试才知道原因。

### P8 应用没有工作表时，按工作表授权的角色创建被拒，错误信息为空

- **谁 / 何时 / 做什么：** 2026-11-23，`hap app role create --type 0 --permission-scope 0`，应用还没有工作表。
- **预期结果：** 允许创建空权限的角色，或者给出明确原因。
- **实际结果：** "The server refused the request (error None)"。改用 permission-scope 20 才成功。
- **影响：** 新应用初始化角色时会卡住。

### P9 CLI 参数在命令之间不一致

- **谁 / 何时 / 做什么：** 2026-11-23，使用 hap-cli 0.9.14。
- **问题：**
  - `worksheet create --fields` 不接受 `@文件`（报 "not valid JSON"），而 `worksheet update-fields --fields @文件` 可以。
  - `worksheet add-fields` 没有 `-a/--app-id`，其他 worksheet 命令都有。
- **影响：** 脚本需要为每个命令写不同的参数形式，长字段列表还会受命令行长度限制。
- 补充（2026-11-23）：`record create` 接受 `--no-workflow`，`record update` 却拒绝它（"Workflows cannot be suppressed for this write"）；隐藏字段的普通更新被拒，需要 `--ignore-rules`。

### P10 field.add 报超时，但字段实际已创建

- **谁 / 何时 / 做什么：** 2026-11-20 首次记录（另一个演示应用）；2026-11-23 字段调查中再次发生，产生了一个重复的电话字段。
- **实际结果：** 报 "Read timed out (read timeout=30)"，CLI 停止，但字段已经存在。
- **影响：** 按提示重试就会建出重复字段。

### P11 大写金额：表单预览与保存值不同

- **谁 / 何时 / 做什么：** 2026-11-23，字段调查（Uppercase 字段，英文）。
- **实际结果：** 预览显示 "TWO HUNDRED THIRTY FOUR"，保存后为 "TWO HUNDRED AND THIRTY-FOUR"。
- **影响：** 打印的金额大写与界面不一致。

### P12 字段类型编号与 CLI 名称对不上

- **对应关系（实际存储 → CLI 名称）：**
  - API 查询（按钮模式）存为 49，CLI 叫 Button；
  - 标签页存为 52，CLI 叫 Section；
  - 分段存为 22，CLI 叫 Divider；
  - 自由连接 21 叫 DynamicLink；
  - 自定义字段存为 type 2 + customtype，CLI 却列 54；
  - 单选无论什么显示方式都存为 11，CLI 还列 9。
- **影响：** 按 CLI 表生成或比对字段，会出错。

### P13 子表的反向字段不出现在 `worksheet fields` 中

- **影响：** 脚本做读改写时，可能漏掉它，或者把它覆盖掉。

### P14 座机字段存有界面看不到的香港国家设置

- **实际结果：** type 4 的 raw 中有 `commcountries` / `defaultarea`（香港），但设置面板不显示这些选项。

### P15 关闭"选项颜色"后，颜色仍被保存

- **影响：** 再次开启时出现旧颜色，看起来像意外。

### P16 单选切换为"进度条"显示后，"允许用户新增选项"被静默关闭

- **实际结果：** `allowadd` 从 1 变为 0，没有提示。
- **影响：** 用户突然不能新增选项。

### P17 用 add-fields 建立指向本表的双向关联时，没有生成反向字段

- **谁 / 何时 / 做什么：** 2026-11-23，在 Contacts 表用 `hap worksheet add-fields` 新增关联字段：dataSource = 本表，advancedSetting.bidirectional = "1"。
- **复现步骤：**
  1. 用上述方式新增"Related Company"字段。
  2. 读回字段列表。
- **预期结果：** 与在界面中新建本表关联一样，自动生成另一侧的多条字段。
- **实际结果：** 字段标记为 bidirectional 1，并预留了 sourceControlId，但表中没有反向字段。要再执行 `hap worksheet pair-relation` 才会建出来。
- **影响：** 脚本以为已经是双向，实际只有单向。上下级联系人列表缺失，界面上也看不出原因。

### P18 他表字段引用地区字段时，record get 返回 JSON 字符串，而源字段返回对象

- **谁 / 何时 / 做什么：** Odoo 复刻项目的 Builder，2026-11-23，在 Companies 表新增他表字段（type 30，仅显示 strDefault "10"），引用联系人的地区字段，然后用 hap-cli 读回记录。
- **复现步骤：**
  1. 关联记录的地区字段值为 `MY|MY-10`。
  2. 用 `hap worksheet record get` 读取引用它的记录。
  3. 同时读取一条直接含地区字段的记录作对照。
- **预期结果：** 两者格式相同，都是 `{"code": ..., "path": ...}` 对象。
- **实际结果：** 他表字段返回字符串 `"{\n  \"code\": \"MY|MY-10\",\n  \"path\": \"马来西亚/雪兰莪\"\n}"`（带换行），直接的地区字段返回对象 `{"code": "MY|MY-14", "path": "马来西亚/吉隆坡"}`。
- **影响：** 集成方和脚本要为同一种值写两套解析。
- **证据：** BUILD-LOG（23 Nov，Companies 与 Bank Accounts 测试记录）。

### P19 他表字段引用电话字段时，表单显示未格式化的号码

- **谁 / 何时 / 做什么：** 2026-11-23，在 Companies 表用他表字段（仅显示）显示联系人的电话（手机类型，默认马来西亚）。
- **复现步骤：**
  1. 联系人电话填 012-345 6789，联系人表单显示 "+60 012 345 6789"。
  2. 打开引用该联系人的 Companies 记录。
- **预期结果：** 他表字段与源字段的显示格式一致。
- **实际结果：** 他表字段显示存储值 "+60123456789"，没有国家区号分隔和号码格式。
- **影响：** 同一个号码在两张表上显示不同，用户会以为数据不一致。
- **证据：** Chrome 界面截图检查（23 Nov，TEST Company）。

### P20 隐藏字段在 record list 中读出为空，record get 才有值

- **谁 / 何时 / 做什么：** Odoo 复刻项目的 Builder，2026-11-23，在 Product Categories 表设置了隐藏的辅助字段（fieldPermission "011"），用 hap-cli 写入后读回。
- **复现步骤：**
  1. 用 `hap worksheet record update ... --ignore-rules` 写入隐藏文本字段（Ancestor Key 1）。
  2. 用 `hap worksheet record list --fields x_product__ancestor_1` 读取。
  3. 用 `hap worksheet record get` 读取同一条记录。
- **预期结果：** 两种读取返回相同的值（读取者是应用管理员）。
- **实际结果：** list 对全部 7 条记录都返回空字符串 ""，get 返回正确的记录 ID。没有任何提示说明字段被隐藏而未返回。
- **影响：** 集成和脚本用列表接口做校验或导出时，会以为数据丢失，或者用空值覆盖真实数据。
- **证据：** BUILD-LOG（23 Nov，Units and Product Categories）。

### P21 CLI 工作流 DSL：日期计算节点的结果被引用为 string_fx_id，界面和服务器使用 date_fx_id

- **谁 / 何时 / 做什么：** Odoo 复刻项目的 Builder，2026-11-23，用 `hap workflow node batch-add` 建"活动状态"工作流：一个日期计算节点（当前时间 +0d，输出日期），分支条件比较"到期日 早于 / 等于 计算结果"。
- **复现步骤：**
  1. 在 batch-add 的分支条件里引用计算节点结果 `{"kind":"field","node":"today","fieldId":"string_fx_id"}`（hap-cli 0.9.14 自检和文档都说文本、日期结果用 string_fx_id，没有 date_fx_id）。
  2. 发布。
- **预期结果：** 条件引用计算结果，可以发布。
- **实际结果：** 发布被拒（"step(s) have no valid operation, or its content is wrong"），界面显示条件值为"Today-Field Deleted"。在界面重新选择后，读回的引用是 `controlId: "date_fx_id"`；改用 date_fx_id 后发布成功，运行结果正确。
- **影响：** 用 CLI 或 MCP 建的日期比较全部发布失败，错误提示看不出原因。
- **证据：** BUILD-LOG（23 Nov，workflow #14）；流程 "Activities - State on save"。

### P22 CLI 工作流 DSL 无法写"关联字段 不为空"条件

- **谁 / 何时 / 做什么：** 2026-11-23，用 batch-add 建联系人同步流程，分支条件为"上级公司 不为空"。
- **复现步骤：**
  1. 条件写 `{"node":"trigger","field":"<关联字段>","op":"not_empty"}`。
  2. 改写原始条件号 `"op":"31"`。
- **预期结果：** 与界面一样可以选择"为空 / 不为空"。
- **实际结果：** 第 1 步被拒（"A relation column has no 'not_empty' comparison. It takes: all_contains, eq, ne"），第 2 步也被拒（"'31' is not a comparison this filter understands"）。CLI 把 not_empty 映射为条件号 7，而关联字段的"不为空"是 31（"为空"是 32）。只能先用占位条件建好，再用 `node save` 写存储格式（conditionId 31），界面显示"Related Company is not empty"。
- **影响：** 关联字段是否为空是最常见的判断之一，用 CLI / MCP 建不出来。

### P23 batch-add 建分支时，带条件的分支丢失名称

- **实际结果：** 只有不带条件的默认分支保留了 `name`，带条件的分支名称为空，界面显示为"Branch"。用 `node rename` 可以补上。
- **影响：** 流程图难读，维护时分不清分支。

### P24 工作流函数中读取地区字段，得到简体中文路径

- **谁 / 何时 / 做什么：** 2026-11-23，在计算节点中用 `CONCAT("[", 地区, "]")` 和 `LEFT(地区, 2)` 读取联系人地区（值 MY|MY-10），写入文本字段。
- **预期结果：** 取得地区代码（MY|MY-10），或至少取得用户界面语言（英文）的路径。
- **实际结果：** 得到 "[马来西亚/雪兰莪] [马来]"。
- **影响：** 无法在工作流里从地区取得国家代码，也无法给非中文用户生成地址文本。只能改用查询条件"国家.地区 包含 联系人.地区"（实测可用）。与 P3 同源。


### P25 CLI 建的函数计算节点默认 0 位小数，数值结果被取整

- **谁 / 何时 / 做什么：** Odoo 复刻项目的 Builder，2026-11-23，用 batch-add 建计算节点（函数模式，输出数字），例如反向汇率 `1 / 汇率`。
- **复现步骤：**
  1. 建函数计算节点，`output_type: number`。
  2. 运行，结果写入 6 位小数的数字字段。
- **预期结果：** 1 / 0.204553 = 4.888709。
- **实际结果：** 写入 5.000000。读回节点配置为 `"number": 0`（小数位数）。DSL 没有设置小数位的参数，界面上的默认值也不清楚；用 `node save` 改为 `"number": 6` 后结果正确。
- **影响：** 单位换算（1/12、0.016667）、汇率、价格计算全部被静默取整，金额错误且没有任何提示。高风险。
- **证据：** BUILD-LOG（23 Nov，workflow #13）；流程 "Settings - Current rate on change"。

### P26 唯一索引：已删除（回收站中）的记录仍占用唯一值

- **谁 / 何时 / 做什么：** 2026-11-23，汇率表有唯一索引（日期 + 货币）。新建一条 SGD 2026-11-23 测试汇率后删除（进回收站），再新建同一日期和货币的汇率。
- **预期结果：** 删除后可以重新建立。
- **实际结果：** 被拒（resultCode 11，"values must be unique and another record already has them"），而 `record list` 里已经没有这条记录。
- **影响：** 用户删掉一条写错的记录后无法重建，只能去回收站彻底删除；报错信息也没有说明冲突的是回收站里的记录。

### P27 CLI 工作流 DSL："清空字段"写入被丢弃或被拒

- **谁 / 何时 / 做什么：** 2026-11-23，用 batch-add 建"更新记录"节点，字段写入 `{"fieldId": ..., "op": "clear"}`（或 `{"kind": "empty"}`，guide 文档的写法）。
- **实际结果：**
  1. 节点只有这一个写入时，CLI 报错 "The step was saved but none of its 1 field write(s) were kept"，整个批次回滚。
  2. 和其他写入放在一起时，"清空"被静默丢弃，其他字段正常保存。联系人流程的"清空公司名称"就是这样丢失的。
  3. `save-action` 用展开格式 `{"fieldValue": "", "isClear": true}` 也报同样的错误。
- **对照：** 界面设置"清空"后，读回为 `{"type": 2, "fieldValue": "", "isClear": true, "addType": 0}`。用 `node save` 原样写入后可以发布并正常运行。"校准单条数据"节点的字段也是这个格式（isClear true）。
- **影响：** 用 CLI / MCP 建的工作流无法清空字段，而且在混合写入时不会报错。

### P28 CLI 工作流 DSL：对"获取多条数据"结果做求和，只保存成计数

- **谁 / 何时 / 做什么：** 2026-11-23，batch-add 建 rollup 节点：`data_source` 为获取多条的节点，`aggregate: "sum"`，`field: <附加价格字段>`。
- **实际结果：** 读回节点没有汇总字段和方式，界面显示"Total count of the multiple data objects obtained"。运行结果是记录数（2），不是附加价格之和。
- **影响：** 价格计算悄悄出错（每个变体售价都多了 2）。界面上这种节点本身只能计数，CLI 却接受 sum 参数而不报错。

### P29 工作流函数计算：公式出错时结果为空，运行记录显示成功

- **谁 / 何时 / 做什么：** 2026-11-24，价格 PBP 的函数计算节点。
- **复现步骤：**
  1. 函数中写 `IF(<选项字段>="Cost", 1, 2)`（单个等号），或对空记录的选项字段使用 `STRING()`，或对空数字做减法。
  2. 运行流程。
- **预期结果：** 公式有错时节点失败并给出原因，或编辑器在保存时提示。
- **实际结果：** 节点状态为成功，结果为空字符串；后续节点拿到空值，最终价格为空。只有逐项拆开公式写入记录才能找到原因（等号要写 `==`，选项要转文字）。
- **影响：** 金额类计算静默出错，排查成本很高。

### P30 发布时，引用分支内部节点的步骤被拒，提示不具体

- **实际结果：** 分支之后的计算节点引用了某条分支内部的节点（调用 PBP 的结果），发布报 "step(s) have no valid operation, or its content is wrong"，没有说明是跨分支引用。
- **影响：** 设计"分支内计算、分支后汇总"的流程时，很难知道为什么不能发布。

### P31 hap-cli `app role set-permissions --permission-way` 会关闭角色的全部应用级开关

- **谁 / 何时 / 做什么：** 2026-11-24，把角色 "Master Data Manager" 从"查看全部"（20）改为"管理全部记录"（80）。
- **复现步骤：** `hap app role set-permissions <appId> <roleId> --permission-way 80`，再用 `app role permissions` 读回。
- **预期结果：** 只改记录范围，其他设置保持不变。
- **实际结果：** 范围变为 80，但 globalPermissions 全部变成 false：新增记录、导入、导出、讨论、打印、附件下载、日志。CLI 也没有单独设置这些开关的选项，只能删除角色后用 `create --global-permissions-json` 重建。
- **影响：** 角色成员突然不能新增记录或导出，而且命令报的是成功。高风险（已有成员的角色不能简单重建）。

### P32 CLI 工作流 DSL：填写节点的字段权限格式写错时返回 HTTP 500

- **实际结果：** `formProperties` 写成对象 `{字段: "readonly"}` 时，服务器返回 "Internal Server Error"，CLI 回滚批次；正确格式是列表 `[{"id": 字段, "permission": "readonly"}]`。
- **影响：** 报错看不出原因，需要读 CLI 源码才能找到格式。

### P33 工作流"查询工作表"节点：筛选条件的动态值为空时，整个流程失败

- **谁 / 何时 / 做什么：** 2026-11-24 00:48，验收测试中新建两条没有填写"地区"的联系人（公司）。
- **复现步骤：**
  1. 工作表事件流程（新增或更新联系人）中，加"获取单条数据 / 查询工作表"节点（Countries 表），筛选条件为"Countries.地区 包含 触发记录.地区"（动态值）。
  2. 节点之后再加"更新记录"节点（写显示名称等）。
  3. 新建一条"地区"为空的联系人。
- **预期结果：** 动态值为空时，有可配置的处理方式（例如视为"未获取到数据"，按节点的"未获取到数据时继续执行"设置继续），或者至少在搭建 / 发布时提示这种风险。
- **实际结果：** 运行状态为"失败"，原因"筛选条件值为空 Region"，后续节点全部不执行。搭建和发布都显示成功，没有任何提示；节点设为"未获取到数据时继续执行"也没有作用。
- **影响：** 只要有一条记录缺少某个可选字段，整个流程就停在中间，记录的其他自动字段（这里是显示名称、商业实体）都没有写入。只能另建流程，用触发条件"地区不为空"绕开。
- **绕开方法（已用）：** 国家查询拆成独立流程 "Contacts - Country from Region"，触发条件为"地区不为空"。

### P34 hap-cli `record create`：因"隐藏"业务规则拒绝写入，原因是被隐藏字段有默认值

- **谁 / 何时 / 做什么：** 2026-11-24 00:47，用 CLI 新建一条"公司"类型的联系人，只写名称、类型和 Active。
- **复现步骤：**
  1. 联系人表有业务规则"Company: hide person fields"：类型 = 公司时隐藏 Address Type（该字段有默认值 Contact）。
  2. `hap worksheet record create <联系人表> --fields-json '[{"id":"name",...},{"id":"company_type","value":"<公司>"}]'`。
- **预期结果：** 与界面一致，记录保存成功（界面新建公司时，隐藏字段的默认值照常写入）。
- **实际结果：** 报 RuleBlocked："Company: hide person fields" makes Address Type hidden on this record, so it cannot be written。请求中并没有写 Address Type，是默认值被当作写入。
- **影响：** 脚本必须加 `--ignore-rules`，而这个参数同时跳过所有其他规则检查。

### P35 hap-cli `record update`：选项字段写入不存在的选项文字时，保存为无效 key

- **谁 / 何时 / 做什么：** 2026-11-24 01:15，验收"新标签"测试，用 CLI 给 TEST 联系人的"标签"（多选，选项集 Contact Tags，允许用户新增选项）写入新标签。
- **复现步骤：** `hap worksheet record update <联系人表> <记录> --fields-json '[{"id":"category_id","value":["TEST Tag"]}]'`，再用 `record get` 读回，并在界面打开记录。
- **预期结果：** 与界面一致：字段允许新增选项时，新选项加入选项集（带颜色）并写入记录；不允许时报错。
- **实际结果：** 命令成功，记录里保存为 `{"key": "TEST Tag", "value": null}`；选项集没有新增；界面显示一个空白的蓝色标签。在界面输入同样的新标签则正常新增（颜色 #1677ff）。
- **影响：** 导入或集成写入的新标签变成看不见的脏数据，筛选和统计都对不上。

### P36 hap-cli `app role set-permissions --permission-way 0 -P`：每表权限没有保存，命令仍报成功

- **谁 / 何时 / 做什么：** 2026-11-24 01:20，把角色 Employee 从"查看全部 + 管理自己"改为按表授权（主数据只读、活动只管自己的）。
- **复现步骤：**
  1. `hap app role set-permissions <appId> <roleId> --permission-way 0 -P '<每表规则 JSON>'`。分别试过 `app role permissions` 读出的 V3 格式（id / recordDataScope），和 CLI 源码实际发送的旧版 `sheets` 格式（sheetId / readLevel / editLevel / removeLevel / canAdd）。
  2. 用 `app role permissions` 和 GetRoleDetail 读回。
- **预期结果：** 每张表的范围按规则保存。
- **实际结果：** 两种格式都返回成功（EditAppRole 返回 1），但每张表的范围保持原值（20/20/20）；只有"自定义"这个总开关生效，结果角色变成"每张表只看自己的"。另外 `-P` 不接受 `@文件`，完整规则又超过 Windows 命令行长度。
- **影响：** 用 CLI 调整已有角色的按表权限会把角色改坏，而且看不出失败。高风险（有成员的角色会马上影响使用）。
- **绕开方法（已用）：** 先改回 50；用 V3 新建角色（见 P37），旧角色改名保留。

### P37 hap-cli `app role create-fine`：新角色的应用级开关全部关闭；读取范围 0 的表退回"本人、全部允许"

- **谁 / 何时 / 做什么：** 2026-11-24 01:25，用 `create-fine` 新建按表授权的 Employee 角色。
- **复现步骤：** `hap app role create-fine <appId> -n Employee --worksheet-permissions '[{"worksheetId":...,"recordDataScope":{"read":100,"edit":0,"delete":0},...}, {"worksheetId":<系统表>,"recordDataScope":{"read":0,"edit":0,"delete":0}}]'`，再用 `app role permissions` 读回。
- **预期结果：** 帮助说明"未指定的项默认允许"；应用级开关（新增记录、导出、讨论、日志、打印、附件下载）为开；读取范围 0 的表无权限。
- **实际结果：** globalPermissions 全部为 false（成员不能新增任何记录）；读取范围 0 的两张表变成 20/20/20，且新增、导入都允许。CLI 发送的 V3 请求里没有 globalPermissions。
- **影响：** 新角色的成员不能新增记录；想隐藏的表反而可以新增和导入。
- **绕开方法（已用）：** 用同一个 V3 接口在请求中带上 8 个 globalPermissions 开关新建；系统表设为只读。

### P38 hap-cli `create-custom-action`（createRelatedRecord）：按钮显示但点击无反应

- **谁 / 何时 / 做什么：** 2026-11-24 10:10，在界面补测联系人上的 "Launch Plan" 按钮。该按钮由 CLI 在 00:22 创建：`hap worksheet create-custom-action <联系人表> --action-spec '{"type":"createRelatedRecord","relationField":"<Plan Launches 关联字段>"}'`。
- **复现步骤：**
  1. 用上面的命令创建"新建关联记录"按钮。
  2. 打开任意一条联系人，点击按钮。
  3. 打开表单设置 › 自定义动作 › 编辑该按钮。
- **预期结果：** 弹出新建 Plan Launch 的表单（在当前记录中新建关联记录）。
- **实际结果：** 点击没有任何反应，也没有报错。按钮编辑器显示 "At linked record 'Associated records have been deleted' Create Plan Launches"，"按钮可用"的"总是 / 满足条件"都没有选中。读取配置：writeObject 2（关联记录）、relationControl 为空、showType 0。在编辑器里改成"当前记录"并选"总是"后（writeObject 1、showType 1），弹窗正常，提交后流程正常运行。
- **影响：** 用 `workflow trigger` 测流程时一切正常，但用户在界面上无法使用这个按钮，只有在界面实测才会发现。
- **绕开方法（已用）：** 在按钮编辑器里改正后保存。另一个按钮 "Rebuild Variants"（立即执行 + 二次确认）的 showType 也是 0，但能正常使用。
---

### Documentation issues (help.nocoly.com, cached 3 Nov 2026)

Details and URLs are in `native-catalogue/docs/*.md`, in each digest's Traps section.

- **D1. Region field:** the docs say regions outside China have two levels and no state codes. Live, Malaysia has country › state › district with ISO codes. (worksheet-1)
- **D2. Export/import:** "paid editions" on its own page, but included in Free on the plan page. (app-roles-portal-plugins)
- **D3. App recycle bin:** 7 days on one page, 60 on another. (app-roles-portal-plugins)
- **D4. Portal domain:** "cannot be changed" on one page, while the role table mentions editing a custom domain. (app-roles-portal-plugins)
- **D5. Plugin Center:** says field plugins are coming later, but a Custom Fields page exists. (app-roles-portal-plugins)
- **D6. International SMS:** 0.34 credits on one page, 2.3 on another. (org-collab-faq-other)
- **D7. Outbound IPs:** the API-request node page lists 2 IPs, the network FAQ lists 5 Hong Kong IPs. (integration-api-ai)
- **D8. API host:** the help page shows `api.mingdao.com`; Nocoly's own schemas use `www.nocoly.com/api`. (integration-api-ai)
- **D9. PDF output price:** CNY 0.15 per file on one page, US$0.03 on the plan page. (workflow-2)
- **D10. OCR price:** 0.15 credits per call on one page, 0.03 per file on another. (integration-api-ai)
- **D11. Mingdao-era content on Nocoly pages:** RMB prices, "Ultimate Edition", and an e-mail sender at `register.mingdao.com`. (app-roles-portal-plugins)
- **D12. Sub-process executions:** the sub-process page says its runs are not counted, then counts them. (workflow-2)
