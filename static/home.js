async function fetchJson(url) {
  const res = await fetch(url);
  return res.json();
}

function renderHealth(data) {
  const box = document.getElementById("healthBox");
  if (!box) return;

  if (!data || data.status !== "ok") {
    box.textContent = "Sistem bilgisi alınamadı.";
    return;
  }

  box.innerHTML = `
    <div>Servis: ${data.service}</div>
    <div>Durum: ${data.status.toUpperCase()}</div>
    <div>Son Çalışma: ${data.last_run || "-"}</div>
  `;
}

function pickConfidenceClass(confidence) {
  const value = String(confidence || "").toLowerCase();
  if (value.includes("yüksek")) return "badge";
  if (value.includes("orta")) return "badge";
  return "badge";
}

function renderWeeklyPicks(data) {
  const meta = document.getElementById("weeklyMeta");
  const summary = document.getElementById("weeklySummary");
  const grid = document.getElementById("weeklyPicks");

  if (!grid || !summary || !meta) return;

  if (!data || !data.picks || data.picks.length === 0) {
    meta.textContent = "-";
    summary.textContent = "Henüz haftalık öneri yok.";
    grid.innerHTML = `<div class="empty-box">İçerik bekleniyor.</div>`;
    return;
  }

  meta.textContent = data.week_label || "-";
  summary.textContent = data.summary || "";

  grid.innerHTML = data.picks.map(item => `
    <article class="stock-card">
      <div class="stock-top">
        <div>
          <div class="stock-symbol">${item.ticker}</div>
          <div class="stock-name">${item.theme || "Makro fırsat"}</div>
        </div>
        <div class="${pickConfidenceClass(item.confidence)}">${item.confidence || "Orta"}</div>
      </div>

      <div class="stock-desc">${item.reason || "Gerekçe bulunamadı."}</div>

      <div class="stock-meta-row">
        ${item.move_range ? `<span class="meta-chip">Hareket: ${item.move_range}</span>` : ""}
        ${item.score !== undefined && item.score !== null ? `<span class="meta-chip">Skor: ${item.score}/10</span>` : ""}
      </div>

      <a class="card-link" href="/stocks/${item.ticker}">Detayı Aç</a>
    </article>
  `).join("");
}

function renderFeaturedStocks(stocks) {
  const grid = document.getElementById("featuredStocks");
  if (!grid) return;

  const list = (stocks || []).slice(0, 6);

  if (list.length === 0) {
    grid.innerHTML = `<div class="empty-box">Hisse listesi bulunamadı.</div>`;
    return;
  }

  grid.innerHTML = list.map(item => `
    <article class="stock-card">
      <div class="stock-top">
        <div>
          <div class="stock-symbol">${item.symbol}</div>
          <div class="stock-name">${item.name}</div>
        </div>
        <div class="badge">${item.sector}</div>
      </div>

      <div class="stock-desc">${item.description || "Açıklama yok."}</div>

      <div class="stock-meta-row">
        ${item.theme ? `<span class="meta-chip">${item.theme}</span>` : ""}
      </div>

      <a class="card-link" href="/stocks/${item.symbol}">Hisseye Git</a>
    </article>
  `).join("");
}

async function initHome() {
  try {
    const [health, weekly, stocks] = await Promise.all([
      fetchJson("/api/health"),
      fetchJson("/api/weekly-picks/latest"),
      fetchJson("/api/stocks")
    ]);

    renderHealth(health);
    renderWeeklyPicks(weekly);
    renderFeaturedStocks(stocks.stocks || []);
  } catch (error) {
    console.error(error);
  }
}

initHome();