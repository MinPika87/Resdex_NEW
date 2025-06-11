"""
Singleton Memory Service to prevent reinitialization
"""

class MemoryServiceSingleton:
    _instance = None
    _memory_service = None
    _session_manager = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryServiceSingleton, cls).__new__(cls)
        return cls._instance
    
    def get_memory_service(self):
        if self._memory_service is None:
            from .memory_service import InMemoryMemoryService
            self._memory_service = InMemoryMemoryService()
            print("🧠 Created persistent memory service")
        return self._memory_service
    
    def get_session_manager(self, app_name="ResDexRootAgent"):
        if self._session_manager is None:
            from .session_manager import ADKSessionManager
            self._session_manager = ADKSessionManager(app_name, self.get_memory_service())
            print("📝 Created persistent session manager")
        return self._session_manager

# Global singleton instance
memory_singleton = MemoryServiceSingleton()