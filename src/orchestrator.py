import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from threading import Thread, Lock

@dataclass
class NodeStatus:
    node_id: str
    healthy: bool
    last_heartbeat: float
    consecutive_failures: int

class Orchestrator:
    def __init__(self, heartbeat_interval: int = 30):
        self.nodes: Dict[str, NodeStatus] = {}
        self.heartbeat_interval = heartbeat_interval
        self.recovery_threshold = 3
        self._lock = Lock()
        self._monitor_thread: Optional[Thread] = None
        self._running = False
        self.logger = logging.getLogger(__name__)

    def register_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id in self.nodes:
                return False
            
            self.nodes[node_id] = NodeStatus(
                node_id=node_id,
                healthy=True,
                last_heartbeat=time.time(),
                consecutive_failures=0
            )
            self.logger.info(f'Node {node_id} registered successfully')
            return True

    def heartbeat(self, node_id: str) -> bool:
        with self._lock:
            if node_id not in self.nodes:
                return False
            
            node = self.nodes[node_id]
            node.last_heartbeat = time.time()
            node.healthy = True
            node.consecutive_failures = 0
            return True

    def get_healthy_nodes(self) -> List[str]:
        with self._lock:
            return [
                node_id for node_id, status in self.nodes.items()
                if status.healthy
            ]

    def _monitor_nodes(self):
        while self._running:
            current_time = time.time()
            
            with self._lock:
                for node_id, status in self.nodes.items():
                    if (current_time - status.last_heartbeat) > self.heartbeat_interval:
                        status.consecutive_failures += 1
                        status.healthy = False
                        
                        if status.consecutive_failures >= self.recovery_threshold:
                            self.logger.warning(
                                f'Node {node_id} exceeded failure threshold. '
                                'Initiating recovery...'
                            )
                            self._initiate_recovery(node_id)
                    
            time.sleep(self.heartbeat_interval / 2)

    def _initiate_recovery(self, node_id: str):
        try:
            # Implementation-specific recovery logic here
            # Could include:
            # 1. Restarting the node process
            # 2. Redistributing workload
            # 3. Notifying administrators
            self.logger.info(f'Attempting recovery for node {node_id}')
            
            # Reset node status after recovery attempt
            with self._lock:
                if node_id in self.nodes:
                    self.nodes[node_id].consecutive_failures = 0
        
        except Exception as e:
            self.logger.error(f'Recovery failed for node {node_id}: {str(e)}')

    def start_monitoring(self):
        if self._monitor_thread is not None:
            return

        self._running = True
        self._monitor_thread = Thread(
            target=self._monitor_nodes,
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info('Node monitoring started')

    def stop_monitoring(self):
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join()
            self._monitor_thread = None
        self.logger.info('Node monitoring stopped')

    def remove_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id not in self.nodes:
                return False
            
            del self.nodes[node_id]
            self.logger.info(f'Node {node_id} removed')
            return True