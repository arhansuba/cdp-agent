# metrics.py
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
import statistics
from database import Database

class PerformanceMetrics:
   """
   Tracks and analyzes performance metrics for CDP agent operations.
   Handles timing, success rates, gas usage, and operation patterns.
   """
   
   def __init__(self, db: Optional[Database] = None):
       self.db = db or Database()
       self.metrics_cache = {}

   @contextmanager
   def track_operation(self, operation_type: str, wallet_address: str):
       """Context manager for tracking operation timing and success."""
       start_time = time.perf_counter()
       try:
           yield
           duration_ms = (time.perf_counter() - start_time) * 1000
           self._record_metric(
               operation_type=operation_type,
               wallet_address=wallet_address,
               duration_ms=duration_ms,
               success=True
           )
       except Exception as e:
           duration_ms = (time.perf_counter() - start_time) * 1000
           self._record_metric(
               operation_type=operation_type,
               wallet_address=wallet_address,
               duration_ms=duration_ms,
               success=False,
               error_type=type(e).__name__
           )
           raise

   def _record_metric(
       self,
       operation_type: str,
       wallet_address: str,
       duration_ms: float,
       success: bool,
       error_type: Optional[str] = None,
       gas_used: Optional[float] = None
   ):
       """Records a single performance metric."""
       metric_data = {
           'operation_type': operation_type,
           'wallet_address': wallet_address,
           'duration_ms': duration_ms,
           'success': success,
           'error_type': error_type,
           'timestamp': datetime.now(),
           'gas_used': gas_used,
           'details': {}
       }
       self.db.record_metric(metric_data)

   def get_operation_stats(
       self,
       operation_type: Optional[str] = None,
       hours: int = 24
   ) -> Dict[str, Any]:
       """
       Get statistical analysis of operations.
       Includes success rates, average duration, and gas usage patterns.
       """
       metrics = self.db.get_performance_metrics(
           operation_type=operation_type,
           time_range_hours=hours
       )
       
       if not metrics:
           return {
               'total_operations': 0,
               'success_rate': 0,
               'avg_duration_ms': 0,
               'avg_gas_used': 0
           }

       total_ops = len(metrics)
       successful_ops = sum(1 for m in metrics if m['success'])
       
       durations = [m['duration_ms'] for m in metrics]
       gas_usage = [m['gas_used'] for m in metrics if m['gas_used'] is not None]
       
       return {
           'total_operations': total_ops,
           'success_rate': (successful_ops / total_ops) * 100,
           'avg_duration_ms': statistics.mean(durations) if durations else 0,
           'min_duration_ms': min(durations) if durations else 0,
           'max_duration_ms': max(durations) if durations else 0,
           'avg_gas_used': statistics.mean(gas_usage) if gas_usage else 0,
           'error_types': self._analyze_errors(metrics)
       }

   def get_wallet_performance(self, wallet_address: str) -> Dict[str, Any]:
       """Analyze performance metrics for a specific wallet."""
       metrics = self.db.get_performance_metrics(hours=720)  # Last 30 days
       wallet_metrics = [m for m in metrics if m['wallet_address'] == wallet_address]
       
       operations_by_type = {}
       for metric in wallet_metrics:
           op_type = metric['operation_type']
           if op_type not in operations_by_type:
               operations_by_type[op_type] = []
           operations_by_type[op_type].append(metric)

       return {
           'total_operations': len(wallet_metrics),
           'operations_by_type': {
               op_type: {
                   'count': len(ops),
                   'success_rate': (sum(1 for o in ops if o['success']) / len(ops)) * 100,
                   'avg_duration_ms': statistics.mean([o['duration_ms'] for o in ops])
               }
               for op_type, ops in operations_by_type.items()
           }
       }

   def _analyze_errors(self, metrics: List[Dict[str, Any]]) -> Dict[str, int]:
       """Analyze error patterns in operations."""
       error_counts = {}
       for metric in metrics:
           if not metric['success'] and metric.get('error_type'):
               error_type = metric['error_type']
               error_counts[error_type] = error_counts.get(error_type, 0) + 1
       return error_counts

   def get_gas_usage_trends(
       self,
       operation_type: Optional[str] = None,
       days: int = 7
   ) -> List[Dict[str, Any]]:
       """Analyze gas usage trends over time."""
       metrics = self.db.get_performance_metrics(
           operation_type=operation_type,
           time_range_hours=days * 24
       )
       
       gas_trends = {}
       for metric in metrics:
           if metric.get('gas_used'):
               date = metric['timestamp'].date()
               if date not in gas_trends:
                   gas_trends[date] = []
               gas_trends[date].append(metric['gas_used'])

       return [
           {
               'date': date.isoformat(),
               'avg_gas_used': statistics.mean(gas_list),
               'total_operations': len(gas_list)
           }
           for date, gas_list in sorted(gas_trends.items())
       ]

   def generate_performance_report(self) -> Dict[str, Any]:
       """Generate comprehensive performance report."""
       return {
           'overall_stats': self.get_operation_stats(hours=24),
           'gas_trends': self.get_gas_usage_trends(days=7),
           'operation_types': {
               op_type: self.get_operation_stats(operation_type=op_type, hours=24)
               for op_type in self._get_unique_operation_types()
           }
       }

   def _get_unique_operation_types(self) -> List[str]:
       """Get list of all unique operation types."""
       metrics = self.db.get_performance_metrics(time_range_hours=720)
       return list(set(m['operation_type'] for m in metrics))