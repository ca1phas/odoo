// Read-only extract of one Odoo model, for nocoly/reference/odoo-19.4/<model>.md.
//
// How to use: log in to casimir.odoo.com, open DevTools › Console, set MODEL below, paste this whole file,
// then run  copy(window.__extract)  to put the result on the clipboard. It only calls read methods
// (fields_get, get_views, default_get, search_read, search_count) — it changes nothing.
//
// What it produces, as compact text:
//   fields  — name | label | type | relation | required | read-only | stored | module | selection | help
//   views   — form, list, kanban and search, as indented outlines keeping the attributes that matter
//             (invisible, required, readonly, placeholder, widget, domain, optional, string)
//   actions — every window action on the model, defaults, _order, SQL constraints, record count
(async () => {
  const MODEL = 'uom.uom';

  const rpc = (model, method, args, kwargs = {}) =>
    fetch(`/web/dataset/call_kw/${model}/${method}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {model, method, args, kwargs}}),
    }).then(r => r.json()).then(r => r.result);

  const KEEP = ['name', 'string', 'invisible', 'required', 'readonly', 'placeholder', 'widget', 'domain',
                'optional', 'column_invisible', 'groups', 'context'];
  const outline = (node, depth, out) => {
    if (node.nodeType !== 1) return;
    if (node.tagName === 'templates' || (node.tagName === 'div' && node.getAttribute('name') === 'button_box')) {
      const inner = [...node.querySelectorAll('field, button')]
        .map(n => (n.tagName === 'button' ? 'btn:' : '') + (n.getAttribute('name') || ''));
      out.push(`${'  '.repeat(depth)}<${node.tagName}${node.getAttribute('name') ? ' name=' + node.getAttribute('name') : ''}> [${inner.join(' ')}]`);
      return;
    }
    const attrs = KEEP.filter(k => node.hasAttribute(k))
      .map(k => `${k}=${JSON.stringify(node.getAttribute(k).replace(/\s+/g, ' '))}`).join(' ');
    const text = [...node.childNodes].filter(c => c.nodeType === 3 && c.textContent.trim())
      .map(c => c.textContent.trim().replace(/\s+/g, ' ')).join(' ');
    if (['div', 'span', 'i'].includes(node.tagName) && !attrs && !text) {
      [...node.children].forEach(ch => outline(ch, depth, out));
      return;
    }
    out.push(`${'  '.repeat(depth)}<${node.tagName}${attrs ? ' ' + attrs : ''}>${text ? ` "${text.slice(0, 80)}"` : ''}`);
    [...node.children].forEach(ch => outline(ch, depth + 1, out));
  };

  const lines = [`MODEL ${MODEL} ${(window.odoo && odoo.info && odoo.info.server_version) || ''}`];

  const fields = await rpc(MODEL, 'fields_get', [], {
    attributes: ['string', 'type', 'relation', 'required', 'readonly', 'store', 'selection', 'help']});
  const modules = Object.fromEntries(((await rpc('ir.model.fields', 'search_read',
    [[['model', '=', MODEL]]], {fields: ['name', 'modules']})) || []).map(f => [f.name, f.modules]));
  lines.push('## FIELDS name | label | type | relation | req | ro | store | module | selection | help');
  for (const [name, f] of Object.entries(fields)) {
    if (['id', 'display_name', 'create_uid', 'create_date', 'write_uid', 'write_date'].includes(name)) continue;
    lines.push([name, f.string, f.type, f.relation || '', f.required ? 'REQ' : '', f.readonly ? 'RO' : '',
                f.store ? 'S' : '-', modules[name] || '', (f.selection || []).map(s => `${s[0]}:${s[1]}`).join(','),
                (f.help || '').replace(/\s+/g, ' ').slice(0, 160)].join(' | '));
  }

  for (const type of ['form', 'list', 'kanban', 'search']) {
    const res = await rpc(MODEL, 'get_views', [[[false, type]]], {options: {}});
    if (!res) continue;
    const out = [];
    outline(new DOMParser().parseFromString(res.views[type].arch, 'text/xml').documentElement, 0, out);
    lines.push(`## VIEW ${type}`, out.join('\n'));
  }

  const actions = await rpc('ir.actions.act_window', 'search_read', [[['res_model', '=', MODEL]]],
    {fields: ['name', 'view_mode', 'context', 'domain']}) || [];
  lines.push('## ACTIONS', ...actions.map(a => [a.name, a.view_mode, a.context, a.domain].join(' | ')));

  const defaults = await rpc(MODEL, 'default_get', [Object.keys(fields)], {});
  lines.push('## DEFAULTS', JSON.stringify(defaults));
  const order = await rpc('ir.model', 'search_read', [[['model', '=', MODEL]]], {fields: ['order']});
  lines.push('## ORDER ' + ((order && order[0] && order[0].order) || ''));
  const constraints = await rpc('ir.model.constraint', 'search_read',
    [[['model.model', '=', MODEL], ['type', '=', 'u']]], {fields: ['name', 'definition', 'message']}) || [];
  lines.push('## SQL CONSTRAINTS', ...constraints.map(c => [c.name, c.definition, c.message].join(' | ')));
  lines.push('## RECORD COUNT (archived included) ' +
             await rpc(MODEL, 'search_count', [[]], {context: {active_test: false}}));

  window.__extract = lines.join('\n');
  console.log(`${MODEL}: ${window.__extract.length} characters — run copy(window.__extract)`);
})();
