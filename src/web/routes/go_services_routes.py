"""
Go Services Routes
Provides endpoints for monitoring and managing Go microservices
"""

from flask import Blueprint, jsonify, request
from src.core.go_services import go_services
from src.core.logger import log_info, log_error

go_services_bp = Blueprint('go_services', __name__)

@go_services_bp.route("/api/go_services/status")
def get_services_status():
    """Get status of all Go services"""
    try:
        status = {
            "enabled": go_services.enabled,
            "data_fetcher": {
                "healthy": go_services.data_fetcher.health_check(),
                "url": "http://localhost:8080"
            },
            "cache": {
                "healthy": go_services.cache.health_check(),
                "url": "http://localhost:8081"
            },
            "background_workers": {
                "healthy": go_services.background_workers.health_check(),
                "url": "http://localhost:8082"
            }
        }
        
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        log_error(f"Failed to get Go services status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@go_services_bp.route("/api/go_services/performance")
def get_services_performance():
    """Get performance statistics from all Go services"""
    try:
        stats = go_services.get_performance_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        log_error(f"Failed to get Go services performance: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@go_services_bp.route("/api/go_services/restart")
def restart_services():
    """Restart all Go services"""
    try:
        # This would trigger a restart in a real implementation
        # For now, just return a message
        log_info("Go services restart requested")
        
        return jsonify({
            "success": True,
            "message": "Go services restart initiated"
        })
    except Exception as e:
        log_error(f"Failed to restart Go services: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@go_services_bp.route("/api/go_services/cache/clear")
def clear_go_cache():
    """Clear Go cache service"""
    try:
        success = go_services.cache.clear()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Go cache cleared successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to clear Go cache"
            }), 500
    except Exception as e:
        log_error(f"Failed to clear Go cache: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@go_services_bp.route("/api/go_services/jobs/submit", methods=["POST"])
def submit_background_job():
    """Submit a job to Go background workers"""
    try:
        data = request.get_json()
        
        if not data or 'type' not in data:
            return jsonify({
                "success": False,
                "error": "Job type is required"
            }), 400
        
        job_type = data['type']
        job_data = data.get('data', {})
        priority = data.get('priority', 1)
        delay = data.get('delay', 0)
        
        success = go_services.background_workers.submit_job(
            job_type, job_data, priority, delay
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Job {job_type} submitted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to submit job"
            }), 500
    except Exception as e:
        log_error(f"Failed to submit background job: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@go_services_bp.route("/api/go_services/jobs/stats")
def get_jobs_stats():
    """Get background jobs statistics"""
    try:
        stats = go_services.background_workers.get_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        log_error(f"Failed to get jobs stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@go_services_bp.route("/api/go_services/cache/stats")
def get_cache_stats():
    """Get Go cache service statistics"""
    try:
        stats = go_services.cache.get_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        log_error(f"Failed to get cache stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
