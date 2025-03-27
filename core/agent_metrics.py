"""Enhanced monitoring system with rolling metrics and trend analysis."""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from collections import defaultdict
import pandas as pd
import numpy as np
from loguru import logger
from dotenv import load_dotenv

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .config import ConfigLoader, SystemConfig

class MetricsCollector:
    """Collects and analyzes agent performance metrics."""
    
    def __init__(
        self,
        config: Optional['ConfigLoader'] = None,
        log_dir: Optional[str] = None,
        metrics_dir: Optional[str] = None
    ):
        """Initialize metrics collector.
        
        Args:
            config: Optional configuration loader
            log_dir: Optional directory for logs
            metrics_dir: Optional directory for metrics
        """
        load_dotenv()
        self.config = config
        
        # Get directories from config or use defaults
        if self.config:
            system_config = self.config.get_system_config()
            if system_config:
                log_dir = log_dir or system_config.log_dir
                metrics_dir = metrics_dir or system_config.metrics_dir
                
        self.log_dir = Path(log_dir or "logs")
        self.metrics_dir = Path(metrics_dir or "metrics")
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Initialize metrics storage
        self.daily_metrics = defaultdict(lambda: defaultdict(list))
        self.rolling_metrics = defaultdict(lambda: defaultdict(list))
        self.agent_metrics = defaultdict(lambda: defaultdict(dict))
        
        # Load existing metrics
        self._load_metrics()
        
    def _load_metrics(self):
        """Load existing metrics from storage."""
        metrics_file = self.metrics_dir / "metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                    self.daily_metrics = defaultdict(lambda: defaultdict(list), data.get('daily', {}))
                    self.rolling_metrics = defaultdict(lambda: defaultdict(list), data.get('rolling', {}))
                    self.agent_metrics = defaultdict(lambda: defaultdict(dict), data.get('agents', {}))
            except Exception as e:
                logger.error(f"Error loading metrics: {e}")
                
    def _save_metrics(self):
        """Save metrics to storage."""
        metrics_file = self.metrics_dir / "metrics.json"
        try:
            with open(metrics_file, 'w') as f:
                json.dump({
                    'daily': dict(self.daily_metrics),
                    'rolling': dict(self.rolling_metrics),
                    'agents': dict(self.agent_metrics)
                }, f)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            
    def collect_daily_metrics(self):
        """Collect metrics from today's logs."""
        today = datetime.now().date()
        today_str = today.isoformat()
        
        # Reset daily metrics
        self.daily_metrics[today_str] = defaultdict(list)
        
        # Process today's logs
        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        timestamp = datetime.fromisoformat(log_entry.get('timestamp', ''))
                        
                        if timestamp.date() != today:
                            continue
                            
                        agent_id = log_entry.get('agent_id', 'unknown')
                        self._process_log_entry(agent_id, log_entry)
                        
                    except json.JSONDecodeError:
                        continue
                        
        # Update rolling metrics
        self._update_rolling_metrics()
        
        # Save metrics
        self._save_metrics()
        
    def _process_log_entry(self, agent_id: str, log_entry: Dict[str, Any]):
        """Process a single log entry and update metrics."""
        today = datetime.now().date().isoformat()
        
        # Basic metrics
        self.daily_metrics[today]['total_tasks'].append(1)
        self.daily_metrics[today]['agent_tasks'][agent_id].append(1)
        
        # Status metrics
        status = log_entry.get('status')
        if status == 'completed':
            self.daily_metrics[today]['completed_tasks'].append(1)
            self.daily_metrics[today]['agent_completed'][agent_id].append(1)
        elif status == 'failed':
            self.daily_metrics[today]['failed_tasks'].append(1)
            self.daily_metrics[today]['agent_failed'][agent_id].append(1)
            
        # Retry metrics
        retry_count = log_entry.get('retry_count', 0)
        if retry_count > 0:
            self.daily_metrics[today]['retries'].append(retry_count)
            self.daily_metrics[today]['agent_retries'][agent_id].append(retry_count)
            
        # Timing metrics
        duration = log_entry.get('duration', 0)
        self.daily_metrics[today]['task_durations'].append(duration)
        self.daily_metrics[today]['agent_durations'][agent_id].append(duration)
        
    def _update_rolling_metrics(self):
        """Update rolling metrics for the past 7 days."""
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=7)
        
        # Clear old rolling metrics
        self.rolling_metrics.clear()
        
        # Aggregate metrics for the past 7 days
        for date in pd.date_range(cutoff_date, today):
            date_str = date.date().isoformat()
            if date_str not in self.daily_metrics:
                continue
                
            daily = self.daily_metrics[date_str]
            
            # Aggregate basic metrics
            self.rolling_metrics['total_tasks'].extend(daily['total_tasks'])
            self.rolling_metrics['completed_tasks'].extend(daily['completed_tasks'])
            self.rolling_metrics['failed_tasks'].extend(daily['failed_tasks'])
            self.rolling_metrics['retries'].extend(daily['retries'])
            self.rolling_metrics['task_durations'].extend(daily['task_durations'])
            
            # Aggregate agent-specific metrics
            for agent_id in set().union(*[set(daily[k].keys()) for k in daily if k.startswith('agent_')]):
                self.rolling_metrics[f'agent_{agent_id}_tasks'].extend(daily['agent_tasks'].get(agent_id, []))
                self.rolling_metrics[f'agent_{agent_id}_completed'].extend(daily['agent_completed'].get(agent_id, []))
                self.rolling_metrics[f'agent_{agent_id}_failed'].extend(daily['agent_failed'].get(agent_id, []))
                self.rolling_metrics[f'agent_{agent_id}_retries'].extend(daily['agent_retries'].get(agent_id, []))
                self.rolling_metrics[f'agent_{agent_id}_durations'].extend(daily['agent_durations'].get(agent_id, []))
                
    def calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends and KPIs."""
        trends = {
            'velocity': self._calculate_velocity(),
            'error_trends': self._calculate_error_trends(),
            'retry_efficiency': self._calculate_retry_efficiency(),
            'agent_kpis': self._calculate_agent_kpis()
        }
        return trends
        
    def _calculate_velocity(self) -> Dict[str, float]:
        """Calculate task completion velocity trends."""
        completed = self.rolling_metrics['completed_tasks']
        if not completed:
            return {'current': 0, 'trend': 0}
            
        # Calculate daily velocities
        daily_velocities = []
        for date in pd.date_range(datetime.now().date() - timedelta(days=7), datetime.now().date()):
            date_str = date.date().isoformat()
            if date_str in self.daily_metrics:
                daily_velocities.append(len(self.daily_metrics[date_str]['completed_tasks']))
                
        if not daily_velocities:
            return {'current': 0, 'trend': 0}
            
        # Calculate trend (slope of velocity over time)
        x = np.arange(len(daily_velocities))
        slope = np.polyfit(x, daily_velocities, 1)[0]
        
        return {
            'current': daily_velocities[-1],
            'trend': slope,
            'daily_velocities': daily_velocities
        }
        
    def _calculate_error_trends(self) -> Dict[str, float]:
        """Calculate error rate trends."""
        total = len(self.rolling_metrics['total_tasks'])
        failed = len(self.rolling_metrics['failed_tasks'])
        
        if total == 0:
            return {'current_rate': 0, 'trend': 0}
            
        # Calculate daily error rates
        daily_rates = []
        for date in pd.date_range(datetime.now().date() - timedelta(days=7), datetime.now().date()):
            date_str = date.date().isoformat()
            if date_str in self.daily_metrics:
                daily_total = len(self.daily_metrics[date_str]['total_tasks'])
                daily_failed = len(self.daily_metrics[date_str]['failed_tasks'])
                if daily_total > 0:
                    daily_rates.append(daily_failed / daily_total)
                    
        if not daily_rates:
            return {'current_rate': 0, 'trend': 0}
            
        # Calculate trend
        x = np.arange(len(daily_rates))
        slope = np.polyfit(x, daily_rates, 1)[0]
        
        return {
            'current_rate': failed / total,
            'trend': slope,
            'daily_rates': daily_rates
        }
        
    def _calculate_retry_efficiency(self) -> Dict[str, float]:
        """Calculate retry efficiency metrics."""
        total_retries = sum(self.rolling_metrics['retries'])
        total_tasks = len(self.rolling_metrics['total_tasks'])
        
        if total_tasks == 0:
            return {'efficiency': 0, 'retry_rate': 0}
            
        # Calculate retry success rate
        retry_success = 0
        for date in pd.date_range(datetime.now().date() - timedelta(days=7), datetime.now().date()):
            date_str = date.date().isoformat()
            if date_str in self.daily_metrics:
                for log_entry in self.daily_metrics[date_str].get('log_entries', []):
                    if log_entry.get('retry_count', 0) > 0 and log_entry.get('status') == 'completed':
                        retry_success += 1
                        
        efficiency = retry_success / total_retries if total_retries > 0 else 0
        retry_rate = total_retries / total_tasks
        
        return {
            'efficiency': efficiency,
            'retry_rate': retry_rate,
            'total_retries': total_retries,
            'successful_retries': retry_success
        }
        
    def _calculate_agent_kpis(self) -> Dict[str, Dict[str, float]]:
        """Calculate KPIs for each agent."""
        kpis = {}
        
        # Get unique agent IDs
        agent_ids = set()
        for key in self.rolling_metrics:
            if key.startswith('agent_'):
                agent_id = key.split('_')[1]
                agent_ids.add(agent_id)
                
        for agent_id in agent_ids:
            tasks = len(self.rolling_metrics[f'agent_{agent_id}_tasks'])
            completed = len(self.rolling_metrics[f'agent_{agent_id}_completed'])
            failed = len(self.rolling_metrics[f'agent_{agent_id}_failed'])
            retries = sum(self.rolling_metrics[f'agent_{agent_id}_retries'])
            durations = self.rolling_metrics[f'agent_{agent_id}_durations']
            
            if tasks == 0:
                continue
                
            kpis[agent_id] = {
                'completion_rate': completed / tasks,
                'error_rate': failed / tasks,
                'retry_rate': retries / tasks,
                'avg_duration': np.mean(durations) if durations else 0,
                'total_tasks': tasks,
                'completed_tasks': completed,
                'failed_tasks': failed,
                'total_retries': retries
            }
            
        return kpis
        
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for the monitoring dashboard."""
        return {
            'trends': self.calculate_trends(),
            'rolling_metrics': dict(self.rolling_metrics),
            'daily_metrics': dict(self.daily_metrics),
            'agent_metrics': dict(self.agent_metrics)
        }
        
    def record_metric(
        self,
        agent_name: str,
        task_type: str,
        task_description: str,
        status: str,
        duration_ms: float,
        retries_attempted: Optional[int] = None,
        retry_success: Optional[bool] = None,
        retry_strategy_used: Optional[str] = None
    ):
        """Record a metric for a task execution."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'agent_id': agent_name,
            'task_type': task_type,
            'description': task_description,
            'status': status,
            'duration': duration_ms,
            'retry_count': retries_attempted,
            'retry_success': retry_success,
            'retry_strategy': retry_strategy_used
        }
        
        # Process the log entry
        self._process_log_entry(agent_name, log_entry)
        
        # Save metrics
        self._save_metrics()

# Global metrics collector instance
metrics_collector = MetricsCollector()

def record_metric(
    agent_name: str,
    task_type: str,
    task_description: str,
    status: str,
    duration_ms: float,
    retries_attempted: Optional[int] = None,
    retry_success: Optional[bool] = None,
    retry_strategy_used: Optional[str] = None
):
    """
    Record a performance metric using the global metrics collector.
    
    Args:
        agent_name: Name of the agent
        task_type: Type of task executed
        task_description: Description of the task
        status: PASS/FAIL or error message
        duration_ms: Duration in milliseconds
        retries_attempted: Number of retry attempts made
        retry_success: Whether the retry was successful
        retry_strategy_used: Type of retry strategy used
    """
    metrics_collector.record_metric(
        agent_name=agent_name,
        task_type=task_type,
        task_description=task_description,
        status=status,
        duration_ms=duration_ms,
        retries_attempted=retries_attempted,
        retry_success=retry_success,
        retry_strategy_used=retry_strategy_used
    ) 