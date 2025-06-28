#!/usr/bin/env python3
"""
Tier Management System
Handles user tier management using the user_tiers database table.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.core.database import get_db_connection
from src.core.logger import log_info, log_error, log_debug

logger = logging.getLogger(__name__)

class TierManager:
    """Manages user tiers and feature access control."""
    
    def __init__(self):
        self.default_user_id = "default"
        self.tier_configs = {
            "free": {
                "level": 0,
                "max_api_calls": 100,
                "max_symbols": 5,
                "features": ["basic_analysis", "system_status"]
            },
            "paid": {
                "level": 1,
                "max_api_calls": 1000,
                "max_symbols": 50,
                "features": [
                    "basic_analysis", "enhanced_analysis", "portfolio", 
                    "backtest", "opportunities", "recommendations", "system_status"
                ]
            }
        }
    
    def get_user_tier(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current tier information for a user."""
        if user_id is None:
            user_id = self.default_user_id
            
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT tier_name, tier_level, features, is_active, updated_at
                        FROM user_tiers 
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    result = cur.fetchone()
                    
                    if result:
                        tier_name, tier_level, features, is_active, updated_at = result
                        
                        # Parse features JSON
                        if isinstance(features, str):
                            features = json.loads(features)
                        elif features is None:
                            features = {}
                        
                        return {
                            "user_id": user_id,
                            "current_tier": tier_name,
                            "tier_level": tier_level,
                            "features": features,
                            "is_active": is_active,
                            "updated_at": updated_at.isoformat() if updated_at else None,
                            "status": "active" if is_active else "inactive"
                        }
                    else:
                        # Create default tier if user doesn't exist
                        return self.create_default_tier(user_id)
                        
        except Exception as e:
            log_error(f"Error getting user tier for {user_id}: {str(e)}")
            return self._get_fallback_tier(user_id)
    
    def create_default_tier(self, user_id: str) -> Dict[str, Any]:
        """Create a default free tier for a new user."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    default_features = json.dumps(self.tier_configs["free"])
                    
                    cur.execute("""
                        INSERT INTO user_tiers (user_id, tier_name, tier_level, features)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            tier_name = EXCLUDED.tier_name,
                            tier_level = EXCLUDED.tier_level,
                            features = EXCLUDED.features,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING tier_name, tier_level, features, is_active, updated_at
                    """, (user_id, "free", 0, default_features))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    if result:
                        tier_name, tier_level, features, is_active, updated_at = result
                        
                        if isinstance(features, str):
                            features = json.loads(features)
                        
                        return {
                            "user_id": user_id,
                            "current_tier": tier_name,
                            "tier_level": tier_level,
                            "features": features,
                            "is_active": is_active,
                            "updated_at": updated_at.isoformat() if updated_at else None,
                            "status": "active" if is_active else "inactive"
                        }
                    else:
                        return self._get_fallback_tier(user_id)
                        
        except Exception as e:
            log_error(f"Error creating default tier for {user_id}: {str(e)}")
            return self._get_fallback_tier(user_id)
    
    def upgrade_tier(self, user_id: str, new_tier: str) -> Dict[str, Any]:
        """Upgrade user to a new tier."""
        if new_tier not in self.tier_configs:
            raise ValueError(f"Invalid tier: {new_tier}. Valid tiers: {list(self.tier_configs.keys())}")
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    tier_config = self.tier_configs[new_tier]
                    features = json.dumps(tier_config)
                    
                    cur.execute("""
                        INSERT INTO user_tiers (user_id, tier_name, tier_level, features)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            tier_name = EXCLUDED.tier_name,
                            tier_level = EXCLUDED.tier_level,
                            features = EXCLUDED.features,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING tier_name, tier_level, features, is_active, updated_at
                    """, (user_id, new_tier, tier_config["level"], features))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    if result:
                        tier_name, tier_level, features, is_active, updated_at = result
                        
                        if isinstance(features, str):
                            features = json.loads(features)
                        
                        log_info(f"User {user_id} upgraded to {new_tier} tier")
                        
                        return {
                            "user_id": user_id,
                            "current_tier": tier_name,
                            "tier_level": tier_level,
                            "features": features,
                            "is_active": is_active,
                            "updated_at": updated_at.isoformat() if updated_at else None,
                            "status": "active" if is_active else "inactive",
                            "message": f"Successfully upgraded to {new_tier} tier"
                        }
                    else:
                        return self._get_fallback_tier(user_id)
                        
        except Exception as e:
            log_error(f"Error upgrading tier for {user_id} to {new_tier}: {str(e)}")
            raise
    
    def check_feature_access(self, user_id: str, feature: str) -> bool:
        """Check if user has access to a specific feature."""
        try:
            tier_info = self.get_user_tier(user_id)
            features = tier_info.get("features", {})
            
            if isinstance(features, dict):
                feature_list = features.get("features", [])
            else:
                feature_list = features if isinstance(features, list) else []
            
            return feature in feature_list
            
        except Exception as e:
            log_error(f"Error checking feature access for {user_id}, feature {feature}: {str(e)}")
            return False
    
    def get_tier_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tier usage statistics."""
        if user_id is None:
            user_id = self.default_user_id
            
        try:
            tier_info = self.get_user_tier(user_id)
            
            # Get API usage stats (placeholder - would need to implement actual tracking)
            api_usage = {
                "total_calls": 0,
                "calls_today": 0,
                "limit": tier_info.get("features", {}).get("max_api_calls", 100)
            }
            
            return {
                "user_id": user_id,
                "current_tier": tier_info["current_tier"],
                "tier_level": tier_info["tier_level"],
                "api_usage": api_usage,
                "features_count": len(tier_info.get("features", {}).get("features", [])),
                "last_updated": tier_info.get("updated_at"),
                "status": tier_info.get("status")
            }
            
        except Exception as e:
            log_error(f"Error getting tier stats for {user_id}: {str(e)}")
            return {
                "user_id": user_id,
                "current_tier": "free",
                "tier_level": 0,
                "api_usage": {"total_calls": 0, "calls_today": 0, "limit": 100},
                "features_count": 2,
                "last_updated": datetime.now().isoformat(),
                "status": "error"
            }
    
    def _get_fallback_tier(self, user_id: str) -> Dict[str, Any]:
        """Get fallback tier information when database is unavailable."""
        return {
            "user_id": user_id,
            "current_tier": "free",
            "tier_level": 0,
            "features": self.tier_configs["free"],
            "is_active": True,
            "updated_at": datetime.now().isoformat(),
            "status": "fallback"
        }
    
    def get_all_tiers(self) -> List[Dict[str, Any]]:
        """Get all available tier configurations."""
        return [
            {
                "name": tier_name,
                "level": config["level"],
                "max_api_calls": config["max_api_calls"],
                "max_symbols": config["max_symbols"],
                "features": config["features"]
            }
            for tier_name, config in self.tier_configs.items()
        ]

# Global tier manager instance
tier_manager = TierManager() 