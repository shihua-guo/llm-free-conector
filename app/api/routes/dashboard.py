from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=["dashboard"])


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> str:
    return DASHBOARD_HTML


DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Model Dashboard</title>
  <style>
    :root {
      --bg: #f5f7f4;
      --ink: #19231d;
      --muted: #66736a;
      --line: #d8ded7;
      --panel: #ffffff;
      --accent: #176b55;
      --accent-soft: #dceee8;
      --warn: #9c4f18;
      --off: #909994;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background:
        linear-gradient(135deg, rgba(23, 107, 85, 0.09), transparent 34%),
        linear-gradient(315deg, rgba(156, 79, 24, 0.08), transparent 38%),
        var(--bg);
      color: var(--ink);
      font-family: "Aptos", "Segoe UI", sans-serif;
      min-height: 100vh;
    }

    header {
      border-bottom: 1px solid var(--line);
      background: rgba(245, 247, 244, 0.88);
      backdrop-filter: blur(10px);
      position: sticky;
      top: 0;
      z-index: 2;
    }

    .wrap {
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px;
    }

    .topline {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
      align-items: center;
    }

    h1 {
      font-family: "Georgia", "Times New Roman", serif;
      font-size: clamp(30px, 4vw, 52px);
      line-height: 1;
      margin: 0 0 8px;
      letter-spacing: 0;
    }

    .sub {
      color: var(--muted);
      margin: 0;
      font-size: 15px;
    }

    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }

    input, button, select {
      height: 40px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      color: var(--ink);
      font: inherit;
    }

    input {
      width: min(280px, 100%);
      padding: 0 12px;
    }

    button {
      padding: 0 14px;
      cursor: pointer;
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      font-weight: 700;
    }

    button.secondary {
      background: var(--panel);
      color: var(--ink);
      border-color: var(--line);
    }

    main.wrap {
      display: grid;
      gap: 18px;
    }

    .summary {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
    }

    .metric, .group {
      background: rgba(255, 255, 255, 0.92);
      border: 1px solid var(--line);
      border-radius: 8px;
    }

    .metric {
      padding: 14px;
      min-height: 88px;
    }

    .metric strong {
      display: block;
      font-size: 30px;
      line-height: 1.1;
    }

    .metric span {
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
    }

    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
    }

    .filters select, .filters input {
      min-width: 190px;
    }

    .status {
      color: var(--muted);
      font-size: 14px;
    }

    .groups {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .group h2 {
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      font-size: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .badge {
      background: var(--accent-soft);
      color: var(--accent);
      border-radius: 999px;
      padding: 4px 9px;
      font-size: 13px;
      font-weight: 700;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }

    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }

    th {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      background: #fafbf9;
    }

    td.model {
      font-family: "Cascadia Code", "Consolas", monospace;
      overflow-wrap: anywhere;
      width: 52%;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    .disabled {
      color: var(--off);
    }

    .priority {
      font-family: "Cascadia Code", "Consolas", monospace;
      white-space: nowrap;
    }

    .empty {
      padding: 28px 16px;
      color: var(--muted);
    }

    @media (max-width: 900px) {
      .topline, .groups, .summary {
        grid-template-columns: 1fr;
      }

      .toolbar {
        justify-content: stretch;
      }

      .toolbar input, .toolbar button {
        flex: 1 1 100%;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap topline">
      <div>
        <h1>Model Dashboard</h1>
        <p class="sub">Synced NewAPI models grouped by fixed routing capability.</p>
      </div>
      <div class="toolbar">
        <input id="token" type="password" autocomplete="off" placeholder="Connector API key">
        <button class="secondary" id="saveToken">Save key</button>
        <button id="refresh">Refresh</button>
      </div>
    </div>
  </header>

  <main class="wrap">
    <section class="summary" id="summary"></section>
    <section class="filters">
      <div>
        <select id="capability">
          <option value="all">All capabilities</option>
          <option value="text">Text</option>
          <option value="embedding">Embedding</option>
          <option value="audio">Audio</option>
          <option value="image">Image</option>
          <option value="video">Video</option>
        </select>
        <input id="search" type="search" placeholder="Filter models">
      </div>
      <div class="status" id="status">Loading...</div>
    </section>
    <section class="groups" id="groups"></section>
  </main>

  <script>
    const order = ["text", "embedding", "audio", "image", "video", "unknown"];
    const tokenInput = document.querySelector("#token");
    const statusEl = document.querySelector("#status");
    const groupsEl = document.querySelector("#groups");
    const summaryEl = document.querySelector("#summary");
    const capabilityEl = document.querySelector("#capability");
    const searchEl = document.querySelector("#search");
    let allModels = [];

    tokenInput.value = localStorage.getItem("connectorToken") || "";

    document.querySelector("#saveToken").addEventListener("click", () => {
      localStorage.setItem("connectorToken", tokenInput.value.trim());
      loadModels();
    });
    document.querySelector("#refresh").addEventListener("click", loadModels);
    capabilityEl.addEventListener("change", render);
    searchEl.addEventListener("input", render);

    async function loadModels() {
      statusEl.textContent = "Loading models...";
      const headers = {};
      const token = tokenInput.value.trim();
      if (token) headers.Authorization = `Bearer ${token}`;

      try {
        const response = await fetch("/admin/models", { headers });
        if (response.status === 401) {
          statusEl.textContent = "Unauthorized. Enter CONNECTOR_API_KEY and save.";
          allModels = [];
          render();
          return;
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        allModels = await response.json();
        statusEl.textContent = `Loaded ${allModels.length} models`;
        render();
      } catch (error) {
        statusEl.textContent = `Load failed: ${error.message}`;
        allModels = [];
        render();
      }
    }

    function render() {
      const capability = capabilityEl.value;
      const query = searchEl.value.trim().toLowerCase();
      const filtered = allModels.filter((model) => {
        const capOk = capability === "all" || model.capability === capability;
        const queryOk = !query || model.model.toLowerCase().includes(query) || model.family.toLowerCase().includes(query);
        return capOk && queryOk;
      });
      renderSummary(filtered);
      renderGroups(filtered);
    }

    function renderSummary(models) {
      const counts = Object.fromEntries(order.map((cap) => [cap, 0]));
      for (const model of models) counts[model.capability || "unknown"] = (counts[model.capability || "unknown"] || 0) + 1;
      summaryEl.innerHTML = order.slice(0, 5).map((cap) => `
        <div class="metric">
          <strong>${counts[cap] || 0}</strong>
          <span>${cap}</span>
        </div>
      `).join("");
    }

    function renderGroups(models) {
      const grouped = new Map(order.map((cap) => [cap, []]));
      for (const model of models) {
        const cap = grouped.has(model.capability) ? model.capability : "unknown";
        grouped.get(cap).push(model);
      }

      groupsEl.innerHTML = order
        .map((cap) => [cap, grouped.get(cap) || []])
        .filter(([, items]) => items.length > 0)
        .map(([cap, items]) => `
          <article class="group">
            <h2>${title(cap)} <span class="badge">${items.length}</span></h2>
            ${table(items)}
          </article>
        `).join("") || `<article class="group"><div class="empty">No models found.</div></article>`;
    }

    function table(items) {
      const rows = items
        .sort((a, b) => priority(a) - priority(b) || a.model.localeCompare(b.model))
        .slice(0, 120)
        .map((item) => `
          <tr class="${item.enabled ? "" : "disabled"}">
            <td class="model">${escapeHtml(item.model)}</td>
            <td>${escapeHtml(item.family || "unknown")}</td>
            <td class="priority">${item.manual_priority ?? item.default_priority}</td>
            <td>${item.enabled ? "on" : "off"}</td>
          </tr>
        `).join("");

      return `
        <table>
          <thead><tr><th>Model</th><th>Family</th><th>Priority</th><th>State</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }

    function priority(item) {
      return item.manual_priority ?? item.default_priority ?? 999999;
    }

    function title(value) {
      return value.charAt(0).toUpperCase() + value.slice(1);
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    loadModels();
  </script>
</body>
</html>
"""
