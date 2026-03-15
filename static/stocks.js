let allStocks = [];
let allPrices = {};
let currentSearch = "";
let currentSector = "ALL";
let currentSort = "NONE";
let priceRefreshInterval = null;

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return res.json();
}

function formatPrice(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  return `$${Number(value).toFixed(2)}`;
}

function formatChangePct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  const num = Number(value);
  const prefix = num > 0 ? "+" : "";
  return `${prefix}%${num.toFixed(2)}`;
}

function getPriceInfo(symbol) {
  return allPrices[symbol] || { price: null, change_pct: null };
}

function getFilteredAndSortedStocks() {
  let result = [...allStocks];

  if (currentSearch) {
    result = result.filter((item) => {
      return (
        String(item.symbol || "").toLowerCase().includes(currentSearch) ||
        String(item.name || "").toLowerCase().includes(currentSearch) ||
        String(item.sector || "").toLowerCase().includes(currentSearch) ||
        String(item.theme || "").toLowerCase().includes(currentSearch)
      );
    });
  }

  if (currentSector !== "ALL") {
    result = result.filter((item) => String(item.sector || "") === currentSector);
  }

  if (currentSort === "PRICE_ASC") {
    result.sort((a, b) => {
      const pa = getPriceInfo(a.symbol).price;
      const pb = getPriceInfo(b.symbol).price;
      return (pa ?? Number.POSITIVE_INFINITY) - (pb ?? Number.POSITIVE_INFINITY);
    });
  } else if (currentSort === "PRICE_DESC") {
    result.sort((a, b) => {
      const pa = getPriceInfo(a.symbol).price;
      const pb = getPriceInfo(b.symbol).price;
      return (pb ?? Number.NEGATIVE_INFINITY) - (pa ?? Number.NEGATIVE_INFINITY);
    });
  } else if (currentSort === "NAME_ASC") {
    result.sort((a, b) => String(a.name || "").localeCompare(String(b.name || ""), "tr"));
  } else if (currentSort === "NAME_DESC") {
    result.sort((a, b) => String(b.name || "").localeCompare(String(a.name || ""), "tr"));
  }

  return result;
}

function renderStocks(stocks) {
  const count = document.getElementById("stocksCount");
  const grid = document.getElementById("stocksGrid");

  if (!count || !grid) return;

  count.textContent = `${stocks.length} hisse gösteriliyor`;

  if (stocks.length === 0) {
    grid.innerHTML = `<div class="empty-box">Sonuç bulunamadı.</div>`;
    return;
  }

  grid.innerHTML = stocks.map((item) => {
    const priceInfo = getPriceInfo(item.symbol);
    const change = priceInfo.change_pct;
    const changeClass =
      change === null || change === undefined
        ? ""
        : Number(change) >= 0
          ? "pos"
          : "neg";

    return `
      <article class="stock-card">
        <div class="stock-top">
          <div>
            <div class="stock-symbol">${item.symbol}</div>
            <div class="stock-name">${item.name}</div>
          </div>
          <div class="badge">${item.sector}</div>
        </div>

        <div class="stock-price-row">
          <div class="stock-price">${formatPrice(priceInfo.price)}</div>
          <div class="stock-change ${changeClass}">${formatChangePct(change)}</div>
        </div>

        <div class="stock-desc">${item.description || "Açıklama yok."}</div>

        <div class="stock-meta-row">
          ${item.theme ? `<span class="meta-chip">${item.theme}</span>` : ""}
        </div>

        <a class="card-link" href="/stocks/${encodeURIComponent(item.symbol)}">Detay Sayfası</a>
      </article>
    `;
  }).join("");
}

function renderSectorOptions() {
  const select = document.getElementById("sectorFilter");
  if (!select) return;

  const sectors = [...new Set(allStocks.map((item) => item.sector).filter(Boolean))].sort((a, b) =>
    String(a).localeCompare(String(b), "tr")
  );

  select.innerHTML = `
    <option value="ALL">Tüm Sektörler</option>
    ${sectors.map((sector) => `<option value="${sector}">${sector}</option>`).join("")}
  `;

  select.value = currentSector;
}

function renderAll() {
  const finalStocks = getFilteredAndSortedStocks();
  renderStocks(finalStocks);
}

function updatePriceInfoText(updatedAt) {
  const el = document.getElementById("priceUpdateInfo");
  if (!el) return;

  if (!updatedAt) {
    el.textContent = "Fiyatlar güncellenemedi.";
    return;
  }

  el.textContent = `Fiyatlar otomatik yenileniyor • Son güncelleme: ${updatedAt}`;
}

function getVisibleTickersForPricing() {
  const finalStocks = getFilteredAndSortedStocks();
  return finalStocks.slice(0, 48).map((item) => item.symbol);
}

async function loadStocks() {
  try {
    const data = await fetchJson("/api/stocks");
    allStocks = data.stocks || [];
    renderSectorOptions();
    renderAll();
  } catch (error) {
    console.error(error);
  }
}

async function loadPrices() {
  try {
    const tickers = getVisibleTickersForPricing();
    if (!tickers.length) {
      updatePriceInfoText(null);
      return;
    }

    const qs = encodeURIComponent(tickers.join(","));
    const data = await fetchJson(`/api/stocks/prices?tickers=${qs}`);

    allPrices = {
      ...allPrices,
      ...(data.prices || {})
    };

    updatePriceInfoText(data.updated_at || null);
    renderAll();
  } catch (error) {
    console.error(error);
    updatePriceInfoText(null);
  }
}

function setupControls() {
  const searchInput = document.getElementById("searchInput");
  const sectorFilter = document.getElementById("sectorFilter");
  const sortFilter = document.getElementById("sortFilter");

  if (searchInput) {
    searchInput.addEventListener("input", async () => {
      currentSearch = String(searchInput.value || "").trim().toLowerCase();
      renderAll();
      await loadPrices();
    });
  }

  if (sectorFilter) {
    sectorFilter.addEventListener("change", async () => {
      currentSector = sectorFilter.value || "ALL";
      renderAll();
      await loadPrices();
    });
  }

  if (sortFilter) {
    sortFilter.addEventListener("change", async () => {
      currentSort = sortFilter.value || "NONE";
      renderAll();
      await loadPrices();
    });
  }
}

async function initStocksPage() {
  setupControls();
  await loadStocks();
  await loadPrices();

  if (priceRefreshInterval) {
    clearInterval(priceRefreshInterval);
  }

  priceRefreshInterval = setInterval(loadPrices, 5000);
}

initStocksPage();