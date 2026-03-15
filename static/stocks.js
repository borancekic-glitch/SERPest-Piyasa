let allStocks = [];

async function fetchJson(url) {
  const res = await fetch(url);
  return res.json();
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

  grid.innerHTML = stocks.map(item => `
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

      <a class="card-link" href="/stocks/${item.symbol}">Detay Sayfası</a>
    </article>
  `).join("");
}

function applyFilter() {
  const input = document.getElementById("searchInput");
  const q = (input?.value || "").trim().toLowerCase();

  if (!q) {
    renderStocks(allStocks);
    return;
  }

  const filtered = allStocks.filter(item => {
    return (
      String(item.symbol).toLowerCase().includes(q) ||
      String(item.name).toLowerCase().includes(q) ||
      String(item.sector).toLowerCase().includes(q) ||
      String(item.theme).toLowerCase().includes(q)
    );
  });

  renderStocks(filtered);
}

async function initStocksPage() {
  try {
    const data = await fetchJson("/api/stocks");
    allStocks = data.stocks || [];
    renderStocks(allStocks);

    const input = document.getElementById("searchInput");
    if (input) {
      input.addEventListener("input", applyFilter);
    }
  } catch (error) {
    console.error(error);
  }
}

initStocksPage();