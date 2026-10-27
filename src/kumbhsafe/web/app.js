"use strict";
const COLORS = {SAFE: "#2e9e5b", MODERATE: "#d9a400", HIGH: "#e8782a", CRITICAL: "#d12f2f"};
const $ = (s) => document.querySelector(s);
const SVGNS = "http://www.w3.org/2000/svg";

function el(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) e[k] = v;
  e.append(...kids);
  return e;
}
function svg(tag, attrs = {}, text) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text !== undefined) e.textContent = text;
  return e;
}
const badge = (lvl) => el("span", {className: "badge " + lvl, textContent: lvl});

async function api(path, body) {
  const opt = body ? {method: "POST", headers: {"Content-Type": "application/json"},
                      body: JSON.stringify(body)} : {};
  const r = await fetch(path, opt);
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || "request failed");
  return data;
}

let facilities = [];

function drawMap(zones) {
  const W = 640, H = 360, pad = 50;
  const pts = zones.concat(facilities);
  const lats = pts.map((p) => p.lat), lons = pts.map((p) => p.lon);
  const [minLa, maxLa, minLo, maxLo] = [Math.min(...lats), Math.max(...lats), Math.min(...lons), Math.max(...lons)];
  const X = (lo) => pad + ((lo - minLo) / (maxLo - minLo || 1)) * (W - 2 * pad);
  const Y = (la) => H - pad - ((la - minLa) / (maxLa - minLa || 1)) * (H - 2 * pad);
  const m = $("#map");
  m.replaceChildren();
  const sym = {hospital: "\u25CF", first_aid: "+", police: "\u25B2", fire: "\u25C6"};
  for (const f of facilities) {
    const t = svg("text", {x: X(f.lon), y: Y(f.lat), "text-anchor": "middle", "font-size": 15, fill: "#4b6cb7"}, sym[f.type] || "?");
    t.append(svg("title", {}, f.name + " (" + f.type + ")"));
    m.append(t);
  }
  for (const z of zones) {
    const r = 12 + Math.min(z.density, 7) * 4;
    const g = svg("g");
    const c = svg("circle", {cx: X(z.lon), cy: Y(z.lat), r, fill: COLORS[z.level], "fill-opacity": 0.55, stroke: COLORS[z.level], "stroke-width": 2});
    c.append(svg("title", {}, z.zone + ": " + z.density + "/m2, " + z.level));
    g.append(c, svg("text", {x: X(z.lon), y: Y(z.lat) + r + 13, "text-anchor": "middle", "font-size": 11, fill: "currentColor"}, z.zone));
    m.append(g);
  }
}

function renderZones(zones) {
  const tb = $("#zones");
  tb.replaceChildren(...zones.map((z) => el("tr", {},
    el("td", {textContent: z.zone}), el("td", {textContent: z.count.toLocaleString()}),
    el("td", {textContent: z.density}), el("td", {textContent: z.growth_pct + "%"}),
    el("td", {}, badge(z.level)))));
  $("#k-people").textContent = zones.reduce((a, z) => a + z.count, 0).toLocaleString();
  $("#k-crit").textContent = zones.filter((z) => z.level === "HIGH" || z.level === "CRITICAL").length;
}

function renderAlerts(alerts) {
  const ul = $("#alerts");
  if (!alerts.length) return ul.replaceChildren(el("li", {textContent: "No active alerts."}));
  ul.replaceChildren(...alerts.map((a) => el("li", {}, badge(a.level), " " + a.message,
    el("small", {textContent: "Nearest medical: " + (a.nearest_medical || "n/a")}))));
}

function incidentLine(i) {
  const where = i.facility ? i.facility + " (" + i.distance_km + " km, ~" + i.eta_min + " min)" : "no facility found";
  return el("li", {}, badge(i.priority), " " + i.kind.toUpperCase() + " | " + i.zone + " | " + i.detail,
    el("small", {textContent: i.time + "  ->  " + where}));
}

async function refresh() {
  try {
    const [zones, alerts, incs] = await Promise.all([api("/api/zones"), api("/api/alerts"), api("/api/incidents")]);
    renderZones(zones); drawMap(zones); renderAlerts(alerts);
    $("#incidents").replaceChildren(...(incs.length ? incs.map(incidentLine) : [el("li", {textContent: "No incidents yet."})]));
    $("#k-inc").textContent = incs.length;
  } catch (e) { console.error(e); }
}

function showOut(sel, node) { const o = $(sel); o.hidden = false; o.replaceChildren(node); }

async function init() {
  const meta = await api("/api/meta");
  facilities = await api("/api/facilities");
  for (const s of document.querySelectorAll(".zone-sel, #surge-zone"))
    s.replaceChildren(...meta.zones.map((z) => el("option", {value: z, textContent: z})));
  $("#sos-type").replaceChildren(...meta.sos_types.map((t) => el("option", {value: t, textContent: t.replace("_", " ")})));
  $("#symptoms").append(...meta.symptoms.map((s) => el("label", {},
    el("input", {type: "checkbox", value: s}), s.replace(/_/g, " "))));

  $("#triage-form").onsubmit = async (ev) => {
    ev.preventDefault();
    const f = ev.target;
    const symptoms = [...f.querySelectorAll("#symptoms input:checked")].map((i) => i.value);
    try {
      const r = await api("/api/triage", {zone: f.zone.value, age: f.age.value, symptoms,
        pregnant: f.pregnant.checked, chronic: f.chronic.checked});
      showOut("#triage-out", el("div", {}, badge(r.priority), " score " + r.score + ": " + r.route));
      refresh();
    } catch (e) { showOut("#triage-out", document.createTextNode("Error: " + e.message)); }
  };
  $("#sos-form").onsubmit = async (ev) => {
    ev.preventDefault();
    const f = ev.target;
    try {
      const r = await api("/api/sos", {zone: f.zone.value, type: f.type.value, note: f.note.value});
      const i = r.incident;
      showOut("#sos-out", el("div", {}, badge(r.priority), " dispatched: " + (i.facility || "none") + " (~" + i.eta_min + " min)"));
      f.note.value = ""; refresh();
    } catch (e) { showOut("#sos-out", document.createTextNode("Error: " + e.message)); }
  };
  $("#surge-btn").onclick = async () => { await api("/api/surge", {zone: $("#surge-zone").value}); refresh(); };

  refresh();
  setInterval(refresh, 2000);
}
init();
