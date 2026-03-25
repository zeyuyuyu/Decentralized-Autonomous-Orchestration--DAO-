import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from threading import Thread, Lock
import json

@dataclass
class NodeHealth:
    node_id: str
    last_heartbeat: float
    status: str
    metrics: Dict

class Orchestrator:
    def __init__(self, heartbeat_interval: int = 30):
        self.nodes: Dict[str, NodeHealth] = {}
        self.lock = Lock()
        self.heartbeat_interval = heartbeat_interval
        self.logger = logging.getLogger(__name__)
        self._monitor_thread: Optional[Thread] = None
        self._running = False

    def start(self):
        """Start the orchestrator and health monitoring"""
        self._running = True
        self._monitor_thread = Thread(target=self._health_monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        self.logger.info('Orchestrator health monitoring started')

    def stop(self):
        """Stop the orchestrator and cleanup"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join()
        self.logger.info('Orchestrator stopped')

    def register_node(self, node_id: str, initial_metrics: Dict = None):
        """Register a new node with the orchestrator"""
        with self.lock:
            self.nodes[node_id] = NodeHealth(
                node_id=node_id,
                last_heartbeat=time.time(),
                status='healthy',
                metrics=initial_metrics or {}
            )
        self.logger.info(f'Node {node_id} registered')

    def update_heartbeat(self, node_id: str, metrics: Dict = None):
        """Update node heartbeat and metrics"""
        with self.lock:
            if node_id in self.nodes:
                self.nodes[node_id].last_heartbeat = time.time()
                self.nodes[node_id].status = 'healthy'
                if metrics:
                    self.nodes[node_id].metrics.update(metrics)

    def get_node_status(self, node_id: str) -> Optional[NodeHealth]:
        """Get current status of a specific node"""
        with self.lock:
            return self.nodes.get(node_id)

    def get_healthy_nodes(self) -> List[str]:
        """Get list of currently healthy nodes"""
        with self.lock:
            return [
                node_id for node_id, health in self.nodes.items()
                if health.status == 'healthy'
            ]

    def _health_monitor_loop(self):
        """Main monitoring loop to check node health"""
        while self._running:
            current_time = time.time()
            with self.lock:
                for node_id, health in self.nodes.items():
                    if (current_time - health.last_heartbeat) > self.heartbeat_interval:
                        if health.status == 'healthy':
                            health.status = 'unhealthy'
                            self.logger.warning(f'Node {node_id} marked unhealthy')
                            self._trigger_recovery(node_id)

            time.sleep(5)  # Check every 5 seconds

    def _trigger_recovery(self, node_id: str):
        """Initiate recovery procedures for unhealthy node"""
        try:
            # Implement recovery logic here
            self.logger.info(f'Initiating recovery for node {node_id}')
            
            # Example recovery steps:
            # 1. Attempt to restart node services
            # 2. Redistribute workload
            # 3. Notify administrators
            
            recovery_data = {
                'node_id': node_id,
                'timestamp': time.time(),
                'action': 'recovery_initiated'
            }
            
            # Log recovery attempt
            self.logger.info(f'Recovery data: {json.dumps(recovery_data)}')
            
        except Exception as e:
            self.logger.error(f'Recovery failed for node {node_id}: {str(e)}')

    def get_system_health(self) -> Dict:
        """Get overall system health metrics"""
        with self.lock:
            total_nodes = len(self.nodes)
            healthy_nodes = len(self.get_healthy_nodes())
            
            return {
                'total_nodes': total_nodes,
                'healthy_nodes': healthy_nodes,
                'health_percentage': (healthy_nodes / total_nodes * 100) if total_nodes > 0 else 0,
                'nodes': {
                    node_id: {
                        'status': health.status,
                        'last_heartbeat': health.last_heartbeat,
                        'metrics': health.metrics
                    } for node_id, health in self.nodes.items()
                }
            }