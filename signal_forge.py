import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import yfinance as yf

REPORTS_DB_FILE = "reports_db.json"
BACKTEST_RESULTS_FILE = "backtest_results.json"


def load_json_file(filename: str, default: Any):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(filename: str, data: Any):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_report_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def get_price_at_date(ticker: str, target_date: datetime) -> Optional[float]:
    """
    Hedef tarihte veya takip eden ilk 5 gün içindeki ilk geçerli işlem gününde 
    kapanış fiyatını çeker. (Hafta sonu/tatil engelini aşar)
    """
    try:
        stock = yf.Ticker(ticker)
        # Hedef tarihten itibaren 5 günlük veri çekerek en yakın işlem gününü buluruz
        start_str = target_date.strftime('%Y-%m-%d')
        end_date = target_date + timedelta(days=5)
        end_str = end_date.strftime('%Y-%m-%d')
        
        hist = stock.history(start=start_str, end=end_str)
        
        if not hist.empty:
            # İlk geçerli satırı (en yakın gün) al
            return float(hist['Close'].iloc[0])
        return None
    except Exception as e:
        print(f"Fiyat çekme hatası ({ticker} @ {target_date}): {e}")
        return None


def run_signal_forge_for_report(report: Dict[str, Any], top_n: int = 5) -> Dict[str, Any]:
    report_id = report.get("id")
    report_date_str = report.get("date")
    report_date = parse_report_date(report_date_str)
    
    scored_stocks = report.get("scored_stocks", [])
    top_stocks = scored_stocks[:top_n]
    
    results = []
    
    if not report_date:
        return {"report_id": report_id, "results": []}

    for stock in top_stocks:
        ticker = stock.get("ticker")
        
        # 1. Giriş Fiyatı (Rapor tarihindeki en yakın fiyat)
        entry_price = get_price_at_date(ticker, report_date)
        
        # 2. 1 Gün Sonraki Fiyat
        day_1_date = report_date + timedelta(days=1)
        day_1_price = get_price_at_date(ticker, day_1_date)
        
        # 3. 5 Gün Sonraki Fiyat
        day_5_date = report_date + timedelta(days=5)
        day_5_price = get_price_at_date(ticker, day_5_date)
        
        # Hesaplamalar
        d1_ret = None
        d5_ret = None
        s1 = None
        s5 = None
        
        if entry_price and day_1_price:
            d1_ret = round(((day_1_price - entry_price) / entry_price) * 100, 2)
            s1 = d1_ret > 0
            
        if entry_price and day_5_price:
            d5_ret = round(((day_5_price - entry_price) / entry_price) * 100, 2)
            s5 = d5_ret > 0

        results.append({
            "report_id": report_id,
            "report_date": report_date_str,
            "ticker": ticker,
            "score": stock.get("score"),
            "price_change_pct": stock.get("price_change_pct"),
            "volume_ratio": stock.get("volume_ratio"),
            "event_supported": stock.get("event_supported"),
            "extract_score": stock.get("extract_score"),
            "reasons": stock.get("reasons", []),
            "entry_price": entry_price,
            "day_1_price": day_1_price,
            "day_5_price": day_5_price,
            "day_1_return_pct": d1_ret,
            "day_5_return_pct": d5_ret,
            "success_1d": s1,
            "success_5d": s5
        })
        
    return {
        "report_id": report_id,
        "report_date": report_date_str,
        "tested_count": len(results),
        "results": results
    }


def save_backtest_result(report_result: Dict[str, Any]):
    results_db = load_json_file(BACKTEST_RESULTS_FILE, [])
    
    # Eskisini silip yenisini ekle (Update mantığı)
    results_db = [r for r in results_db if r.get("report_id") != report_result.get("report_id")]
    results_db.append(report_result)
    
    save_json_file(BACKTEST_RESULTS_FILE, results_db)


def summarize_signal_forge_results(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {}
    
    valid_1d = [r for r in rows if r.get("success_1d") is not None]
    valid_5d = [r for r in rows if r.get("success_5d") is not None]
    
    win_1d = [r for r in valid_1d if r.get("success_1d") is True]
    win_5d = [r for r in valid_5d if r.get("success_5d") is True]
    
    return {
        "total_signals": len(rows),
        "win_rate_1d": round((len(win_1d) / len(valid_1d) * 100), 1) if valid_1d else 0,
        "win_rate_5d": round((len(win_5d) / len(valid_5d) * 100), 1) if valid_5d else 0,
        "avg_return_1d": round(sum(r['day_1_return_pct'] for r in valid_1d) / len(valid_1d), 2) if valid_1d else 0,
        "avg_return_5d": round(sum(r['day_5_return_pct'] for r in valid_5d) / len(valid_5d), 2) if valid_5d else 0
    }


def load_reports_db():
    if not os.path.exists(REPORTS_DB_FILE):
        return []
    with open(REPORTS_DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def run_signal_forge_all(top_n: int = 5) -> Dict[str, Any]:
    reports = load_reports_db()
    if not reports:
        return {"status": "error", "message": "Rapor bulunamadı."}

    all_rows = []
    for report in reports:
        res = run_signal_forge_for_report(report, top_n=top_n)
        save_backtest_result(res)
        all_rows.extend(res.get("results", []))

    summary = summarize_signal_forge_results(all_rows)
    return {"status": "ok", "tested_signals": len(all_rows), "summary": summary}


def run_signal_forge_latest(top_n: int = 5) -> Dict[str, Any]:
    reports = load_reports_db()
    if not reports:
        return {"status": "error", "message": "Rapor bulunamadı."}

    latest_report = reports[0]
    result = run_signal_forge_for_report(latest_report, top_n=top_n)
    save_backtest_result(result)
    
    summary = summarize_signal_forge_results(result.get("results", []))
    return {
        "status": "ok",
        "processed_reports": 1,
        "tested_signals": len(result.get("results", [])),
        "summary": summary
    }


def load_backtest_results():
    return load_json_file(BACKTEST_RESULTS_FILE, [])