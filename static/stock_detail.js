let chart;
let candleSeries;
let volumeSeries;
let currentTicker = null;
let currentRange = "5d";

async function fetchJson(url) {
  const res = await fetch(url);
  return res.json();
}

function formatPercent(value) {
  if (value === null || value === undefined) return "-";
  return `%${value}`;
}

function renderMarketData(payload) {
  const box = document.getElementById("marketDataBox");
  if (!box) return;

  if (!payload || payload.status !== "ok") {
    box.innerHTML = `<div class="metric-card">Piyasa verisi alınamadı.</div>`;
    return;
  }

  const m = payload.market_data;
  const changeClass = Number(m.price_change_pct) >= 0 ? "pos" : "neg";

  box.innerHTML = `
    <div class="metric-card">
      <div class="metric-label">Son Kapanış</div>
      <div class="metric-value">${m.last_close ?? "-"}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Günlük Değişim</div>
      <div class="metric-value ${changeClass}">${formatPercent(m.price_change_pct)}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Son Hacim</div>
      <div class="metric-value">${m.last_volume ?? "-"}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">5G Hacim Oranı</div>
      <div class="metric-value">${m.volume_ratio ?? "-"}x</div>
    </div>
  `;
}

function renderProfile(payload) {
  const nameEl = document.getElementById("stockName");
  const metaEl = document.getElementById("stockMeta");
  const signalBox = document.getElementById("latestSignalBox");

  if (!nameEl || !metaEl || !signalBox) return;

  if (!payload || payload.status !== "ok") {
    metaEl.textContent = "Hisse bilgisi alınamadı.";
    signalBox.textContent = "Son sinyal bilgisi yok.";
    return;
  }

  const stock = payload.stock;
  const signal = payload.latest_signal;

  nameEl.textContent = `${stock.symbol} · ${stock.name}`;
  metaEl.textContent = `${stock.sector}${stock.theme ? " • " + stock.theme : ""}`;

  if (!signal) {
    signalBox.innerHTML = `Bu hisse için son raporda kayıtlı bir sinyal bulunamadı.`;
    return;
  }

  signalBox.innerHTML = `
    <div><strong>Skor:</strong> ${signal.score ?? "-"}/10</div>
    <div><strong>Günlük değişim:</strong> %${signal.price_change_pct ?? "-"}</div>
    <div><strong>Hacim oranı:</strong> ${signal.volume_ratio ?? "-"}x</div>
    <div><strong>Event desteği:</strong> ${signal.event_supported ? "Var" : "Yok"}</div>
    <div style="margin-top:10px;"><strong>Nedenler:</strong> ${(signal.reasons || []).join(", ") || "-"}</div>
  `;
}

function setAiStatus(text) {
  const el = document.getElementById("aiStatus");
  if (el) el.textContent = text;
}

function renderList(items) {
  if (!Array.isArray(items) || items.length === 0) {
    return `<div class="ai-text">Veri yok.</div>`;
  }

  return `<ul>${items.map(item => `<li>${item}</li>`).join("")}</ul>`;
}

function renderAiAnalysis(payload) {
  const box = document.getElementById("aiAnalysisBox");
  if (!box) return;

  if (!payload || payload.status !== "ok") {
    box.innerHTML = `
      <div class="locked-box">
        AI analizi alınamadı.
      </div>
    `;
    return;
  }

  const a = payload.analysis;

  box.innerHTML = `
    <div class="ai-card">
      <div class="ai-top">
        <div>
          <div class="stock-symbol">${a.ticker}</div>
          <div class="stock-name">${a.company_name || a.ticker}</div>
        </div>
        <div class="badge">${a.predicted_direction || "Değişken"}</div>
      </div>

      <div class="ai-section">
        <div class="metric-label">Zaman Ufku</div>
        <div class="ai-text">${a.time_horizon || "1-2 ay"}</div>
      </div>

      <div class="ai-section">
        <div class="metric-label">Tahmini Hareket</div>
        <div class="ai-text"><strong>${a.predicted_direction || "Değişken"}</strong></div>
      </div>

      <div class="ai-section">
        <div class="metric-label">Yön Özeti</div>
        <div class="ai-text">${a.direction_summary || "-"}</div>
      </div>

      <div class="ai-columns">
        <div class="ai-list-box">
          <div class="metric-label">Sektör / Makro Sebepleri</div>
          ${renderList(a.macro_sector_reasons)}
        </div>

        <div class="ai-list-box">
          <div class="metric-label">Şirket Bazlı Sebepler</div>
          ${renderList(a.company_reasons)}
        </div>
      </div>

      <div class="ai-list-box">
        <div class="metric-label">Şirketin Genel Finansal Durumu</div>
        ${renderList(a.financial_reasons)}
      </div>

      <div class="ai-list-box">
        <div class="metric-label">Analizde Kullanılan Haberler</div>
        ${renderList(a.news_used)}
      </div>

      <div class="premium-note">${a.premium_note || ""}</div>
    </div>
  `;
}

function createChart() {
  const chartContainer = document.getElementById("priceChart");
  if (!chartContainer || !window.LightweightCharts) {
    setChartStatus("Grafik kütüphanesi yüklenemedi.");
    return false;
  }

  chartContainer.innerHTML = "";

  const {
    createChart,
    CandlestickSeries,
    HistogramSeries,
    CrosshairMode
  } = window.LightweightCharts;

  chart = createChart(chartContainer, {
    width: chartContainer.clientWidth,
    height: 420,
    layout: {
      background: { color: "#12202d" },
      textColor: "#b9c7d5"
    },
    grid: {
      vertLines: { color: "rgba(255,255,255,0.05)" },
      horzLines: { color: "rgba(255,255,255,0.05)" }
    },
    rightPriceScale: {
      borderColor: "rgba(255,255,255,0.08)"
    },
    timeScale: {
      borderColor: "rgba(255,255,255,0.08)",
      timeVisible: true,
      secondsVisible: false
    },
    crosshair: {
      mode: CrosshairMode.Normal
    }
  });

  candleSeries = chart.addSeries(CandlestickSeries, {
    upColor: "#22c55e",
    downColor: "#ff5d5d",
    borderVisible: false,
    wickUpColor: "#22c55e",
    wickDownColor: "#ff5d5d"
  });

  volumeSeries = chart.addSeries(HistogramSeries, {
    priceFormat: {
      type: "volume"
    },
    priceScaleId: ""
  });

  volumeSeries.priceScale().applyOptions({
    scaleMargins: {
      top: 0.8,
      bottom: 0
    }
  });

  window.addEventListener("resize", () => {
    if (chart && chartContainer.clientWidth) {
      chart.applyOptions({ width: chartContainer.clientWidth });
    }
  });

  return true;
}

function setChartStatus(text) {
  const el = document.getElementById("chartStatus");
  if (el) el.textContent = text;
}

function setActiveRange(range) {
  document.querySelectorAll(".chart-range-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.range === range);
  });
}

async function loadChart(ticker, range = "5d") {
  setChartStatus("Grafik yükleniyor...");

  try {
    const payload = await fetchJson(`/api/stocks/${ticker}/chart?range=${range}`);

    if (!payload || payload.status !== "ok" || !payload.chart?.points?.length) {
      setChartStatus("Grafik verisi alınamadı.");
      return;
    }

    const points = payload.chart.points;
    const candles = points.map(p => ({
      time: p.time,
      open: p.open,
      high: p.high,
      low: p.low,
      close: p.close
    }));

    const volumes = points.map(p => ({
      time: p.time,
      value: p.volume,
      color: p.close >= p.open ? "rgba(34,197,94,0.55)" : "rgba(255,93,93,0.55)"
    }));

    if (!chart) {
      const ok = createChart();
      if (!ok) return;
    }

    if (!candleSeries || !volumeSeries) {
      setChartStatus("Grafik serileri oluşturulamadı.");
      return;
    }

    candleSeries.setData(candles);
    volumeSeries.setData(volumes);
    chart.timeScale().fitContent();

    setChartStatus(`Gösterilen aralık: ${payload.chart.range.toUpperCase()}`);
  } catch (error) {
    console.error(error);
    setChartStatus("Grafik yüklenemedi.");
  }
}

function setupChartRangeButtons(ticker) {
  document.querySelectorAll(".chart-range-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const range = btn.dataset.range;
      currentRange = range;
      setActiveRange(range);
      await loadChart(ticker, range);
    });
  });
}

async function loadAiAnalysis(ticker, forceRefresh = false) {
  setAiStatus(forceRefresh ? "Yenileniyor..." : "Analiz hazırlanıyor...");

  const box = document.getElementById("aiAnalysisBox");
  if (box) {
    box.innerHTML = `
      <div class="locked-box">
        AI analiz hazırlanıyor...
      </div>
    `;
  }

  try {
    const url = forceRefresh
      ? `/api/stocks/${ticker}/ai-analysis?refresh=1`
      : `/api/stocks/${ticker}/ai-analysis`;

    const payload = await fetchJson(url);
    renderAiAnalysis(payload);

    if (payload?.source === "ai") {
      setAiStatus("Canlı AI");
    } else if (payload?.source === "cache") {
      setAiStatus("Cache");
    } else {
      setAiStatus("Fallback");
    }
  } catch (error) {
    console.error(error);
    setAiStatus("Hata");
    renderAiAnalysis({ status: "error" });
  }
}

function setupAiButtons(ticker) {
  const btn = document.getElementById("aiButton");
  const refreshBtn = document.getElementById("refreshAiButton");

  if (btn) {
    btn.addEventListener("click", () => {
      loadAiAnalysis(ticker, false);
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadAiAnalysis(ticker, true);
    });
  }
}

async function initStockDetail() {
  const body = document.body;
  const ticker = body.dataset.ticker;
  const notFound = body.dataset.notFound === "true";

  const notFoundBox = document.getElementById("notFoundBox");
  const stockHeader = document.getElementById("stockHeader");

  if (notFound) {
    if (notFoundBox) notFoundBox.classList.remove("hidden");
    if (stockHeader) stockHeader.classList.add("hidden");
    return;
  }

  currentTicker = ticker;

  setupAiButtons(ticker);
  setupChartRangeButtons(ticker);
  setActiveRange(currentRange);

  try {
    const [profile, marketData] = await Promise.all([
      fetchJson(`/api/stocks/${ticker}`),
      fetchJson(`/api/stocks/${ticker}/market-data`)
    ]);

    renderProfile(profile);
    renderMarketData(marketData);
    await loadChart(ticker, currentRange);
  } catch (error) {
    console.error(error);
    setChartStatus("Grafik yüklenemedi.");
  }
}

initStockDetail();