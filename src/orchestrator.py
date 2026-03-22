import asyncio
import aiohttp
from typing import Dict, List, Optional
import logging

class ServiceOrchestrator:
    def __init__(self):
        self.services: Dict[str, Dict] = {}
        self.health_check_interval = 30  # seconds
        self.logger = logging.getLogger(__name__)

    async def register_service(self, service_id: str, endpoint: str, health_check_path: str = '/health'):
        """Register a new service for orchestration"""
        self.services[service_id] = {
            'endpoint': endpoint,
            'health_check_path': health_check_path,
            'status': 'unknown',
            'last_check': None
        }
        self.logger.info(f'Registered service {service_id} at {endpoint}')

    async def check_service_health(self, service_id: str) -> bool:
        """Check health status of a specific service"""
        service = self.services.get(service_id)
        if not service:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{service['endpoint']}{service['health_check_path']}"
                async with session.get(url, timeout=5) as response:
                    healthy = response.status == 200
                    service['status'] = 'healthy' if healthy else 'unhealthy'
                    service['last_check'] = asyncio.get_event_loop().time()
                    return healthy
        except Exception as e:
            self.logger.error(f'Health check failed for {service_id}: {str(e)}')
            service['status'] = 'unhealthy'
            service['last_check'] = asyncio.get_event_loop().time()
            return False

    async def monitor_services(self):
        """Continuous monitoring of all registered services"""
        while True:
            tasks = []
            for service_id in self.services:
                tasks.append(self.check_service_health(service_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self.logger.info('Health check complete for all services')
            await asyncio.sleep(self.health_check_interval)

    def get_healthy_services(self) -> List[str]:
        """Return list of currently healthy service IDs"""
        return [sid for sid, svc in self.services.items() 
                if svc['status'] == 'healthy']

    def get_service_status(self, service_id: str) -> Optional[Dict]:
        """Get current status of a specific service"""
        return self.services.get(service_id)

    async def start(self):
        """Start the orchestrator"""
        self.logger.info('Starting service orchestrator')
        await self.monitor_services()

# Usage Example:
# async def main():
#     orchestrator = ServiceOrchestrator()
#     await orchestrator.register_service('auth-service', 'http://auth:8080')
#     await orchestrator.register_service('api-gateway', 'http://gateway:8000')
#     await orchestrator.start()