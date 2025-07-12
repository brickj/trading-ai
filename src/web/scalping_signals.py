from flask import Blueprint, render_template, jsonify, request
from src.core.database import get_db_connection, execute_query
from src.core.scalping_analyzer import scalping_analyzer
from src.core.logger import log_info, log_error, log_warning
from datetime import datetime, date
import json
import psycopg2.extras

scalping_signals_bp = Blueprint("scalping_signals", __name__)

@scalping_signals_bp.route("/scalping_signals")
def scalping_signals_page():
    """Scalping signals page - shows historical signals"""
    signals = []
    try:
        log_info("[SCALPING] GET /scalping_signals page requested")
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT ticker, asset_type, date, time_collected, price_open, price_now, 
                           volume_ratio, price_change_pct, gap_pct, sentiment_class, 
                           recommendation, headlines_json
                    FROM scalping_signals
                    ORDER BY date DESC, time_collected DESC
                    LIMIT 100
                """)
                for row in cur.fetchall():
                    # headlines_json is a JSONB column; parse for template
                    headlines = []
                    if row['headlines_json']:
                        try:
                            headlines = json.loads(row['headlines_json'])
                        except Exception:
                            headlines = []
                    signals.append({
                        'ticker': row['ticker'],
                        'asset_type': row['asset_type'],
                        'date': row['date'],
                        'time_collected': row['time_collected'],
                        'price_open': row['price_open'],
                        'price_now': row['price_now'],
                        'volume_ratio': row['volume_ratio'],
                        'price_change_pct': row['price_change_pct'],
                        'gap_pct': row['gap_pct'],
                        'sentiment_class': row['sentiment_class'],
                        'recommendation': row['recommendation'],
                        'headlines': headlines
                    })
        log_info(f"[SCALPING] Loaded {len(signals)} signals for page render")
    except Exception as e:
        import traceback
        log_error(f"[SCALPING] Error loading scalping signals: {e}\n{traceback.format_exc()}")
        print(f"Error loading scalping signals: {e}\n{traceback.format_exc()}")
    return render_template("scalping_signals.html", signals=signals)

@scalping_signals_bp.route("/api/scalping/opportunities", methods=["GET"])
def get_scalping_opportunities():
    """API endpoint to get current scalping opportunities"""
    try:
        log_info("[SCALPING] GET /api/scalping/opportunities called")
        result = scalping_analyzer.get_scalping_opportunities_api()
        log_info(f"[SCALPING] Returning {len(result.get('data', []))} opportunities, total_signals={result.get('total_signals')}, opportunities={result.get('opportunities')}")
        return jsonify(result)
    except Exception as e:
        log_error(f"[SCALPING] Error getting scalping opportunities: {e}")
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "total_signals": 0,
            "opportunities": 0,
            "data": []
        }), 500

@scalping_signals_bp.route("/api/scalping/run_analysis", methods=["POST"])
def run_scalping_analysis():
    """API endpoint to manually trigger scalping analysis"""
    try:
        log_info("[SCALPING] POST /api/scalping/run_analysis triggered")
        opportunities = scalping_analyzer.run_morning_scalping_analysis()
        log_info(f"[SCALPING] Analysis completed. Found {len(opportunities)} opportunities.")
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": f"Analysis completed. Found {len(opportunities)} opportunities.",
            "opportunities": opportunities
        })
    except Exception as e:
        log_error(f"[SCALPING] Error running scalping analysis: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@scalping_signals_bp.route("/api/scalping/today", methods=["GET"])
def get_todays_signals():
    """API endpoint to get today's scalping signals"""
    try:
        log_info("[SCALPING] GET /api/scalping/today called")
        signals = scalping_analyzer.get_todays_scalping_signals()
        log_info(f"[SCALPING] Returning {len(signals)} signals for today")
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "signals": signals,
            "count": len(signals)
        })
    except Exception as e:
        log_error(f"[SCALPING] Error getting today's signals: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@scalping_signals_bp.route("/api/scalping/history", methods=["GET"])
def get_scalping_history():
    """API endpoint to get historical scalping signals"""
    try:
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 100, type=int)
        log_info(f"[SCALPING] GET /api/scalping/history called with days={days}, limit={limit}")
        query = """
        SELECT ticker, asset_type, date, time_collected, price_open, price_now,
               volume_ratio, price_change_pct, gap_pct, sentiment_class, 
               recommendation, headlines_json
        FROM scalping_signals
        WHERE date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY date DESC, time_collected DESC
        LIMIT %s
        """
        results = execute_query(query, (days, limit))
        signals = []
        if results:
            for row in results:
                if isinstance(row, dict):
                    signal = dict(row)
                    # Parse headlines JSON
                    if signal.get('headlines_json'):
                        try:
                            signal['headlines'] = json.loads(signal['headlines_json'])
                        except:
                            signal['headlines'] = []
                    signals.append(signal)
        log_info(f"[SCALPING] Returning {len(signals)} historical signals for days={days}")
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "days": days,
            "signals": signals,
            "count": len(signals)
        })
    except Exception as e:
        log_error(f"[SCALPING] Error getting scalping history: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@scalping_signals_bp.route("/api/scalping/opportunities_by_type", methods=["GET"])
def get_opportunities_by_type():
    """API endpoint to get opportunities filtered by type"""
    try:
        asset_type = request.args.get('type', 'all')
        recommendation = request.args.get('recommendation', 'all')
        log_info(f"[SCALPING] GET /api/scalping/opportunities_by_type called with type={asset_type}, recommendation={recommendation}")
        query = """
        SELECT ticker, asset_type, date, time_collected, price_open, price_now,
               volume_ratio, price_change_pct, gap_pct, sentiment_class, 
               recommendation, headlines_json
        FROM scalping_signals
        WHERE date = CURRENT_DATE
        """
        params = []
        if asset_type != 'all':
            query += " AND asset_type = %s"
            params.append(asset_type)
        if recommendation != 'all':
            query += " AND recommendation = %s"
            params.append(recommendation)
        query += " ORDER BY volume_ratio DESC, price_change_pct DESC"
        results = execute_query(query, tuple(params) if params else None)
        signals = []
        if results:
            for row in results:
                if isinstance(row, dict):
                    signal = dict(row)
                    # Parse headlines JSON
                    if signal.get('headlines_json'):
                        try:
                            signal['headlines'] = json.loads(signal['headlines_json'])
                        except:
                            signal['headlines'] = []
                    signals.append(signal)
        log_info(f"[SCALPING] Returning {len(signals)} filtered opportunities for type={asset_type}, recommendation={recommendation}")
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "asset_type": asset_type,
            "recommendation": recommendation,
            "signals": signals,
            "count": len(signals)
        })
    except Exception as e:
        log_error(f"[SCALPING] Error getting opportunities by type: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@scalping_signals_bp.route("/api/scalping/stats", methods=["GET"])
def get_scalping_stats():
    """API endpoint to get scalping statistics"""
    try:
        log_info("[SCALPING] GET /api/scalping/stats called")
        # Get today's stats
        today_query = """
        SELECT 
            COUNT(*) as total_signals,
            COUNT(CASE WHEN recommendation IN ('Long Scalping Opportunity', 'Short Scalping Opportunity') THEN 1 END) as opportunities,
            COUNT(CASE WHEN asset_type = 'stock' THEN 1 END) as stocks,
            COUNT(CASE WHEN asset_type = 'crypto' THEN 1 END) as cryptos,
            AVG(volume_ratio) as avg_volume_ratio,
            AVG(ABS(price_change_pct)) as avg_price_change,
            COUNT(CASE WHEN sentiment_class = 'Bullish' THEN 1 END) as bullish_count,
            COUNT(CASE WHEN sentiment_class = 'Bearish' THEN 1 END) as bearish_count,
            COUNT(CASE WHEN sentiment_class = 'Neutral' THEN 1 END) as neutral_count
        FROM scalping_signals
        WHERE date = CURRENT_DATE
        """
        today_results = execute_query(today_query)
        today_stats = today_results[0] if today_results else {}
        # Get weekly stats
        weekly_query = """
        SELECT 
            COUNT(*) as total_signals,
            COUNT(CASE WHEN recommendation IN ('Long Scalping Opportunity', 'Short Scalping Opportunity') THEN 1 END) as opportunities
        FROM scalping_signals
        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """
        weekly_results = execute_query(weekly_query)
        weekly_stats = weekly_results[0] if weekly_results else {}
        log_info(f"[SCALPING] Returning stats: today={today_stats}, weekly={weekly_stats}")
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "today": today_stats,
            "weekly": weekly_stats
        })
    except Exception as e:
        log_error(f"[SCALPING] Error getting scalping stats: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@scalping_signals_bp.route("/api/scalping/setup", methods=["POST"])
def setup_scalping_tables():
    """API endpoint to setup scalping tables"""
    try:
        log_info("[SCALPING] POST /api/scalping/setup called")
        success = scalping_analyzer.create_tables_if_not_exists()
        if success:
            log_info("[SCALPING] Scalping tables created/verified successfully")
            return jsonify({
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Scalping tables created/verified successfully"
            })
        else:
            log_error("[SCALPING] Failed to create scalping tables")
            return jsonify({
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": "Failed to create scalping tables"
            }), 500
    except Exception as e:
        log_error(f"[SCALPING] Error setting up scalping tables: {e}")
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500
