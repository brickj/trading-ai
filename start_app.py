#!/usr/bin/env python3
"""
Trading AI - Cross-Platform App Starter with Enhanced Logging
=============================================================

Easy startup script for the Trading AI application with comprehensive logging.
Works on Windows, macOS, and Linux.

Usage:
    python start_app.py
"""

import os
import sys
import subprocess
import socket
import platform
import time
import traceback
from pathlib import Path
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from pathlib import Path
import sys

# Set project root and src path
project_root = Path(__file__).parent.resolve()
src_path = project_root / "src"

# Add both to sys.path
for path in [str(project_root), str(src_path)]:
    if path not in sys.path:
        sys.path.insert(0, path)




# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

    @classmethod
    def disable_on_windows(cls):
        """Disable colors on Windows if not supported"""
        if platform.system() == 'Windows':
            cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.CYAN = cls.NC = ''

# Initialize colors
Colors.disable_on_windows()

def print_status(message):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def print_success(message):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def print_header():
    print(f"{Colors.CYAN}🚀 Starting Trading AI Application with Enhanced Logging...{Colors.NC}")
    print("=" * 60)

def setup_logging():
    """Initialize the logging system"""
    try:
        # Create logs directory
        logs_dir = Path('logs')
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
            print_success("Created logs directory")

        # Initialize logging system
        from src.core.logger import trading_logger, log_system_event, log_info

        log_system_event("=== TRADING AI APPLICATION STARTUP ===", "INFO")
        log_system_event(f"Python Version: {sys.version}", "INFO")
        log_system_event(f"Working Directory: {os.getcwd()}", "INFO")
        log_system_event(f"Script Path: {__file__}", "INFO")

        # Check environment
        use_go_services = os.getenv('USE_GO_SERVICES', 'false').lower() == 'true'
        log_system_event(f"Go Services Enabled: {use_go_services}", "INFO")

        print_success("Enhanced logging system initialized")
        return True
    except ImportError as e:
        print_warning(f"Logging system not available: {e}")
        print_warning("Continuing without enhanced logging...")
        return False

def check_project_directory():
    """Check if we're in the correct project directory"""
    app_file = Path("src/web/app.py")
    if not app_file.exists():
        print_error("Please run this script from the trading project root directory")
        print_error("Expected to find: src/web/app.py")
        return False

    print_success("Found Trading AI project files")
    return True

def check_virtual_environment():
    """Check and activate virtual environment if available"""
    venv_paths = [".venv", "venv", ".env"]

    for venv_path in venv_paths:
        if Path(venv_path).exists():
            print_success(f"Found virtual environment: {venv_path}")

            # Check if we're already in a virtual environment
            if sys.prefix != sys.base_prefix:
                print_status("Already running in virtual environment")
                return True
            else:
                print_warning("Virtual environment found but not activated")
                print_status(f"Activate with: source {venv_path}/bin/activate (Linux/Mac)")
                print_status(f"           or: {venv_path}\\Scripts\\activate (Windows)")
                return True

    print_warning("No virtual environment found")
    print_status("Create one with: python -m venv .venv")
    return False

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'flask',
        'psycopg2',
        'requests',
        'flask_socketio'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print_warning(f"Missing packages: {', '.join(missing_packages)}")
        print_status("Install with: pip install -r requirements.txt")
        return False
    else:
        print_success("All required dependencies found")
        return True

def check_postgresql():
    """Check PostgreSQL connection"""
    try:
        # Try to connect to PostgreSQL
        result = subprocess.run([
            'psql', '-h', 'localhost', '-U', 'trading_user', '-d', 'trading_db',
            '-c', 'SELECT 1;'
        ], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            print_success("PostgreSQL connection working")
            return True
        else:
            print_warning("PostgreSQL connection issue - cache will use fallback")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_warning("PostgreSQL not accessible - cache will use fallback")
        print_status("To fix: Make sure PostgreSQL is running and database is set up")
        return False

def check_port(port=5001):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', port))
    sock.close()

    if result == 0:
        print_warning(f"Port {port} is already in use")
        return False
    else:
        print_success(f"Port {port} is available")
        return True

def kill_existing_processes():
    """Kill existing app processes"""
    try:
        if platform.system() == 'Windows':
            subprocess.run(['taskkill', '/f', '/im', 'python.exe'],
                         capture_output=True)
        else:
            # More targeted kill for Flask apps
            subprocess.run(['pkill', '-f', 'flask'], capture_output=True)
            subprocess.run(['pkill', '-f', 'socketio'], capture_output=True)
            subprocess.run(['lsof', '-ti:5001'], capture_output=True).stdout
            if result := subprocess.run(['lsof', '-ti:5001'], capture_output=True).stdout.strip():
                subprocess.run(['kill', '-9'] + result.decode().split(), capture_output=True)

        print_status("Stopped existing processes")
        time.sleep(2)
        return True
    except:
        print_warning("Could not stop existing processes")
        return False

def get_local_ip():
    """Get local IP address"""
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "your-ip"

def print_app_info():
    """Print application information"""
    local_ip = get_local_ip()

    print()
    print(f"{Colors.CYAN}🔗 Application will be available at:{Colors.NC}")
    print(f"   📱 Local:   http://localhost:5001")
    print(f"   🌐 Network: http://{local_ip}:5001")
    print()
    print(f"{Colors.CYAN}📊 Available pages:{Colors.NC}")
    print("   🏠 Dashboard:     http://localhost:5001/")
    print("   📈 Stocks:        http://localhost:5001/stocks")
    print("   💰 Crypto:        http://localhost:5001/crypto")
    print("   🎯 Opportunities: http://localhost:5001/opportunities")
    print("   ⚙️  System Status: http://localhost:5001/system_status")
    print("   🔍 Logs Viewer:   http://localhost:5001/logs")
    print()
    print(f"{Colors.CYAN}⚡ Features enabled:{Colors.NC}")
    print("   🗄️  PostgreSQL cache (2,400x performance improvement)")
    print("   🚀 Smart batching (5-10x faster bulk analysis)")
    print("   📡 WebSocket real-time progress updates")
    print("   🤖 Ollama AI sentiment analysis (local & free)")
    print("   📊 Enhanced logging system with web viewer")
    print()
    print(f"{Colors.CYAN}🔥 Log Files Available:{Colors.NC}")
    print("   📝 app.log - General application events")
    print("   🌐 api_calls.log - API requests and responses")
    print("   ❌ errors.log - Errors and exceptions")
    print("   ⚡ performance.log - Timing and performance metrics")
    print("   👤 user_actions.log - User interactions and clicks")
    print("   🖥️  system.log - System status and health")
    print()
    print(f"{Colors.YELLOW}🛑 Press Ctrl+C to stop the application{Colors.NC}")
    print("=" * 60)

def start_app():
    """Start the Flask application with enhanced logging"""
    try:
        print_status("Starting Flask application with SocketIO and enhanced logging...")

        # Change to the project directory
        os.chdir(Path(__file__).parent)

        # Import and start Flask app with logging
        try:
            from src.core.logger import log_system_event, log_info, log_exception
            from src.web.app import create_app

            log_info("Successfully imported Flask app components", "system")
            log_system_event("Starting Flask application via create_app", "INFO")

            print_success("Flask application components loaded")
            print_status("Starting server on http://localhost:5001")

            # Start the Flask application - create_app() will handle the server startup
            # with the correct port configuration (5001)
            try:
                create_app()
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    print_error(f"Port 5001 is already in use. Please close the application using port 5001 and try again.")
                else:
                    print_error(f"Failed to start the application: {e}")
                return False

        except ImportError as e:
            print_error(f"Failed to import Flask components: {e}")
            print_error("Make sure all dependencies are installed:")
            print_error("  pip install -r requirements.txt")
            return False

    except KeyboardInterrupt:
        print()
        print_status("Application stopped by user")
        try:
            from src.core.logger import log_system_event
            log_system_event("Application stopped by user (Ctrl+C)", "INFO")
        except:
            pass
    except Exception as e:
        print_error(f"Failed to start application: {e}")
        try:
            from src.core.logger import log_exception
            log_exception("Application startup failure", e)
        except:
            pass
        return False

    return True

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import traceback

def run_scheduled_jobs():
    """Load job schedules from DB and schedule them with APScheduler."""
    from src.data.preload_news_opportunities import preload_news_opportunities
    from src.data.preload_watchlist_opportunities import preload_watchlist_opportunities
    from src.core.database import get_db_connection, ensure_job_schedules_table
    from src.core.scalping_analyzer import scalping_analyzer
    from datetime import datetime, timedelta
    import calendar
    
    # Define preload_stock_data as a placeholder (will be handled by app.py scheduler)
    def preload_stock_data():
        print("[SCHEDULER] preload_stock_data called - this will be handled by the main app scheduler")
    
    # Ensure job_schedules table exists
    ensure_job_schedules_table()
    
    # Check if today is a trading day (Monday-Friday)
    today = datetime.now()
    is_trading_day = today.weekday() < 5  # Monday=0, Friday=4
    
    scheduler = BackgroundScheduler()
    job_map = {
        'preload_news_opportunities': preload_news_opportunities,
        'preload_watchlist_opportunities': preload_watchlist_opportunities,
        'preload_stock_data': preload_stock_data,
        'run_scalping_analysis': lambda: scalping_analyzer.run_morning_scalping_analysis()
    }
    
    # If it's a trading day and the app is starting, run any missed jobs from today
    if is_trading_day:
        print(f"[SCHEDULER] Today ({today.strftime('%A')}) is a trading day. Checking for missed jobs...")
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT id, job_name, run_time, enabled FROM job_schedules WHERE enabled = TRUE')
                    jobs = cur.fetchall()
                    
                    for row in jobs:
                        job_id, job_name, run_time, enabled = row
                        if job_name in job_map:
                            hour, minute, *_ = str(run_time).split(':')
                            scheduled_time = today.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
                            
                            # If the scheduled time has passed today, run the job immediately
                            if scheduled_time < today:
                                print(f"[SCHEDULER] Running missed job: {job_name} (scheduled for {scheduled_time.strftime('%H:%M')})")
                                try:
                                    job_map[job_name]()
                                    # Update last_run to now
                                    cur.execute('UPDATE job_schedules SET last_run = NOW() WHERE id = %s', (job_id,))
                                    conn.commit()
                                    print(f"[SCHEDULER] Completed missed job: {job_name}")
                                except Exception as e:
                                    print(f"[SCHEDULER ERROR] Missed job {job_name} failed: {e}")
        except Exception as e:
            print(f"[SCHEDULER ERROR] Failed to run missed jobs: {e}")
    else:
        print(f"[SCHEDULER] Today ({today.strftime('%A')}) is not a trading day. Skipping missed job check.")
    
    def update_last_run(job_id):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE job_schedules SET last_run = NOW() WHERE id = %s', (job_id,))
                conn.commit()
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id, job_name, run_time, enabled FROM job_schedules WHERE enabled = TRUE')
                jobs = cur.fetchall()
                
                if not jobs:
                    print("[SCHEDULER] No enabled jobs found in database. Setting up default jobs...")
                    # Run the job setup script
                    try:
                        from src.utils.setup_job_scheduler import setup_default_jobs
                        if setup_default_jobs():
                            # Re-query for jobs after setup
                            cur.execute('SELECT id, job_name, run_time, enabled FROM job_schedules WHERE enabled = TRUE')
                            jobs = cur.fetchall()
                        else:
                            print("[SCHEDULER ERROR] Failed to set up default jobs")
                    except ImportError:
                        print("[SCHEDULER ERROR] Could not import job setup script")
                
                for row in jobs:
                    job_id, job_name, run_time, enabled = row
                    if job_name in job_map:
                        hour, minute, *_ = str(run_time).split(':')
                        def job_wrapper(jid=job_id, jname=job_name):
                            try:
                                print(f"[SCHEDULER] Running job: {jname}")
                                job_map[jname]()
                                update_last_run(jid)
                                print(f"[SCHEDULER] Completed job: {jname}")
                            except Exception as e:
                                print(f"[SCHEDULER ERROR] Job {jname} failed: {e}\n{traceback.format_exc()}")
                        
                        scheduler.add_job(
                            job_wrapper,
                            CronTrigger(hour=int(hour), minute=int(minute), day_of_week='mon-fri'),
                            id=f"job_{job_id}",
                            name=job_name,
                            replace_existing=True
                        )
                        print(f"[SCHEDULER] Scheduled {job_name} at {hour}:{minute} (Mon-Fri)")
                    else:
                        print(f"[SCHEDULER WARNING] Unknown job: {job_name}")
        
        scheduler.start()
        print(f"[SCHEDULER] Started scheduler with {len(scheduler.get_jobs())} jobs")
        
    except Exception as e:
        print(f"[SCHEDULER ERROR] Failed to schedule jobs: {e}\n{traceback.format_exc()}")

def main():
    """Main function"""
    from src.core.startup import run_startup_checks
    print_header()

    # Start the update logic in a background thread
    update_thread = threading.Thread(target=run_startup_checks, daemon=True)
    update_thread.start()

    # Check project directory
    if not check_project_directory():
        sys.exit(1)

    # Setup logging system
    logging_enabled = setup_logging()

    # Check virtual environment
    check_virtual_environment()

    # Check dependencies
    if not check_dependencies():
        print_error("Missing dependencies. Please install them first.")
        sys.exit(1)

    # Check PostgreSQL
    check_postgresql()

    # Check if port is available
    if not check_port():
        print_status("Attempting to free port 5001...")
        kill_existing_processes()

        if not check_port():
            print_error("Could not free port 5001. Please stop the process manually.")
            print_status("Try: lsof -ti:5001 | xargs kill -9")
            sys.exit(1)

    # Print application information
    print_app_info()

    # Start the job scheduler
    run_scheduled_jobs()

    # Start the application (web server)
    if not start_app():
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Try to get the current working directory
        current_dir = os.getcwd()
        print(f"Current directory: {current_dir}")
    except OSError as e:
        print(f"Error getting current directory: {e}")

    try:
        # Try to get the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))
        print(f"Project root: {project_root}")
    except OSError as e:
        print(f"Error getting project root: {e}")

    main()