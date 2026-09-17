from fastapi import APIRouter
from backend.core.device_manager import device_manager
from backend.config.settings import settings

router = APIRouter()

@router.get("/health")
def health_check():
    """
    Returns application status and hardware device details.
    """
    # Build device status dict
    device = device_manager.get_device()
    cuda_available = device_manager.cuda_available
    
    info = {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "device": device,
        "cuda_available": cuda_available
    }
    
    # Optional GPU information
    if cuda_available:
        import torch
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["cuda_version"] = torch.version.cuda
        if torch.cuda.is_initialized():
            free_mem, total_mem = torch.cuda.mem_get_info()
            info["gpu_memory_total_gb"] = round(total_mem / (1024 ** 3), 2)
            info["gpu_memory_free_gb"] = round(free_mem / (1024 ** 3), 2)
            
    return info
