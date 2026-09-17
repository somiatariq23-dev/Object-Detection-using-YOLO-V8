import torch
import logging
import threading
from backend.core.logging_config import logger

class DeviceManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(DeviceManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger("app.device_manager")
        self.cuda_available = torch.cuda.is_available()
        self.device = "cuda" if self.cuda_available else "cpu"
        self._initialized = True
        self.logger.info(f"DeviceManager initialized. Selected device: {self.device}")
        self.print_device_info()

    def get_device(self) -> str:
        """
        Returns the selected device name ('cuda' or 'cpu').
        """
        return self.device

    def print_device_info(self):
        """
        Logs and displays hardware configurations, including CUDA version, device name, and memory stats.
        """
        self.logger.info("--- Hardware Device Information ---")
        if self.cuda_available:
            try:
                gpu_name = torch.cuda.get_device_name(0)
                cuda_version = torch.version.cuda
                device_props = torch.cuda.get_device_properties(0)
                total_memory_gb = device_props.total_memory / (1024 ** 3)
                
                self.logger.info(f"GPU Available: True")
                self.logger.info(f"GPU Name: {gpu_name}")
                self.logger.info(f"CUDA Version: {cuda_version}")
                self.logger.info(f"Total GPU Memory: {total_memory_gb:.2f} GB")
                
                # Check current allocations if active
                if torch.cuda.is_initialized():
                    free_mem, total_mem = torch.cuda.mem_get_info()
                    free_gb = free_mem / (1024 ** 3)
                    self.logger.info(f"Free GPU Memory: {free_gb:.2f} GB / {total_memory_gb:.2f} GB")
            except Exception as e:
                self.logger.error(f"Error querying detailed GPU properties: {e}")
        else:
            self.logger.info("GPU Available: False (Running on CPU)")
            # Try to log CPU hardware info if possible, but keep it simple
            import platform
            self.logger.info(f"CPU Processor: {platform.processor() or 'Generic CPU'}")
            self.logger.info(f"Python Version: {platform.python_version()}")
        self.logger.info("----------------------------------")

# Convenient access to singleton
device_manager = DeviceManager()
