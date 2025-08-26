"""
Services module for business logic layer
"""

from .analysis_service import AnalysisService
from .backtest_service import BacktestService  
from .data_service import DataService
from .report_service import ReportService

# Create service instances (singletons for performance)
analysis_service = AnalysisService()
backtest_service = BacktestService()
data_service = DataService()
report_service = ReportService()

__all__ = [
    'AnalysisService',
    'BacktestService', 
    'DataService',
    'ReportService',
    'analysis_service',
    'backtest_service',
    'data_service', 
    'report_service'
]

