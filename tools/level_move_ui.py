"""Offline placement-move controls for LoL2 and LoL3 plan pages."""
import json

from level_edit import document, fields
import level_edit_data as game


CONTROLS = """
<button id="move-toggle" type="button" aria-expanded="false" aria-controls="move-editor">Move a placement</button>
<section id="move-editor" hidden>
<h2>Placement moves</h2>
<label for="move-id">Item or prop</label><select id="move-id"></select>
<p class="muted" id="move-anchor">Choose a placement to outline its stored location.</p>
<fieldset id="move-fields" disabled><legend>New coordinates</legend>
<label>X <input id="move-x" type="number" min="-32768" max="32767" step="1"></label>
<label>{axis} <input id="move-y" type="number" min="-32768" max="32767" step="1"></label>
<button id="move-pick" type="button" aria-pressed="false">Pick on the plan</button>
<button id="move-stage" type="button">Stage move</button>
</fieldset>
<p id="move-status" role="status" class="muted"></p>
<button id="move-export" type="button">Download changes</button>
<button id="move-reset" type="button" disabled>Clear moves</button>
<p class="muted">Apply the change file with <code>tools/level_edit.py</code>.</p>
</section>
"""

STYLE = """
#move-editor{border-bottom:1px solid var(--border);padding:0 0 .7rem;margin-bottom:.7rem}
#move-editor fieldset{border:1px solid var(--border);padding:.5rem;margin:0 0 .6rem}
#move-editor fieldset label{display:inline-block;max-width:48%}
#move-editor input{width:100%}
#move-toggle{margin-bottom:.6rem}
#move-preview{pointer-events:none}
#move-status{min-height:1.4em}
.picking{cursor:crosshair}
"""

SCRIPT = r"""
{
const model = JSON.parse(document.getElementById('move-model').textContent);
const field = id => document.getElementById('move-' + id);
const map = document.getElementById('map');
const panel = field('editor');
const moves = new Map();
const sites = new Map(model.sites.map(row => [row[0], row.slice(1)]));
const preview = document.createElementNS('http://www.w3.org/2000/svg', 'g');
preview.id = 'move-preview';
map.append(preview);
const chooser = field('id');
const xInput = field('x'), yInput = field('y');
const pick = field('pick');
let picking = false;

function graphic(tag, attributes) {
    const shape = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attributes)) shape.setAttribute(key, value);
    return shape;
}
function svgPoint([x, y]) {
    const [a, b, s] = model.transform;
    return [a + x*s, b - y*s];
}
function inside(points, xy) {
    const [x, y] = xy;
    let result = false;
    for (let i = 0; i < points.length; i++) {
        const [a,b] = points[i], [c,d] = points[(i + 1) % points.length];
        if ((c-a)*(y-b) === (d-b)*(x-a) && Math.min(a,c) <= x && x <= Math.max(a,c) &&
            Math.min(b,d) <= y && y <= Math.max(b,d)) return true;
        if ((b > y) !== (d > y) && x < a + (y-b)*(c-a)/(d-b)) result = !result;
    }
    return result;
}
function draw() {
    preview.replaceChildren();
    const site = sites.get(chooser.value);
    if (panel.hidden || !site) return;
    const [, anchor, x, y] = site;
    preview.append(graphic('polygon', {
        points: model.outline[anchor].map(svgPoint).map(p => p.join(',')).join(' '),
        stroke:'#f2c46b', 'stroke-width':1.35, fill:'#f2c46b24'
    }));
    const [cx,cy] = svgPoint(moves.get(chooser.value) || [x,y]);
    preview.append(graphic('circle', {cx, cy, r:3.1, fill:'#f2c46b', stroke:'#14171a', 'stroke-width':1.4}));
}
function setPicking(state) {
    picking = state;
    pick.setAttribute('aria-pressed', String(state));
    map.classList.toggle('picking', state);
}
function status(text) { field('status').textContent = text || moves.size + ' staged'; }
function choose() {
    setPicking(false);
    const site = sites.get(chooser.value);
    field('fields').disabled = !site;
    if (site) {
        const [, anchor, x, y] = site;
        field('anchor').textContent = 'Keep the placement inside ' + model.anchor.toLowerCase() + ' ' + anchor + '.';
        [xInput.value, yInput.value] = moves.get(chooser.value) || [x, y];
    } else {
        field('anchor').textContent = 'Choose a placement to outline its stored location.';
        xInput.value = yInput.value = '';
    }
    draw();
}
function stage() {
    const [, anchor, x, y] = sites.get(chooser.value);
    const xy = [xInput.valueAsNumber, yInput.valueAsNumber];
    if (!xy.every(Number.isInteger) || !xInput.checkValidity() || !yInput.checkValidity()) {
        status('Enter two whole coordinates in the signed 16-bit range.');
        return;
    }
    if (!inside(model.outline[anchor], xy)) {
        status('The destination is outside the highlighted area.');
        return;
    }
    if (xy[0] === x && xy[1] === y) moves.delete(chooser.value);
    else moves.set(chooser.value, xy);
    status();
    field('reset').disabled = !moves.size;
    draw();
}
field('toggle').onclick = () => {
    panel.hidden = !panel.hidden;
    field('toggle').textContent = panel.hidden ? 'Move a placement' : 'Close placement editor';
    field('toggle').setAttribute('aria-expanded', String(!panel.hidden));
    setPicking(false);
    draw();
};
chooser.replaceChildren(new Option('Choose a placement', ''),
    ...model.sites.map(([id, label]) => new Option(label, id)));
chooser.onchange = choose;
document.addEventListener('plan-selected', event => {
    if (!panel.hidden && sites.has(event.detail)) {
        chooser.value = event.detail;
        choose();
    }
});
pick.onclick = () => {
    setPicking(!picking);
    status(picking ? 'Click the highlighted area to fill in the coordinates.' : '');
};
map.addEventListener('click', event => {
    if (!picking) return;
    event.stopPropagation();
    const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(map.getScreenCTM().inverse());
    const [a,b,s] = model.transform;
    xInput.value = Math.round((p.x-a)/s);
    yInput.value = Math.round((b-p.y)/s);
    setPicking(false);
    status('Check the coordinates, then stage the move.');
}, true);
field('stage').onclick = stage;
field('reset').onclick = () => {
    moves.clear();
    field('reset').disabled = true;
    status();
    choose();
};
field('export').onclick = () => {
    const change = {...model.change, moves:[...moves].map(([id, xy]) => [id, ...xy])};
    const url = URL.createObjectURL(new Blob([JSON.stringify(change, null, 2) + '\n'], {type:'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = model.change.level.toLowerCase() + '-moves.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
};
status();
}
"""


def sections(plan, level, raw):
    outline, sites = fields(raw)
    labels = {row["id"]: row["label"] for row in plan.records}
    anchors = {site.anchor for site in sites.values()}
    model = {"change": document(level, raw, []), "anchor": game.ANCHOR,
             "outline": {i: [[x / 65536, y / 65536] for x, y in outline[i]] for i in sorted(anchors)},
             "sites": [[p.key, labels[p.key], p.anchor, p.x, p.y] for p in sites.values()],
             "transform": [*plan.point((0, 0)), plan.scale * 65536]}
    raw = json.dumps(model, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c")
    return (CONTROLS.format(axis=game.AXIS), f'<style>{STYLE}</style>'
            f'<script id="move-model" type="application/json">{raw}</script><script>{SCRIPT}</script>')
