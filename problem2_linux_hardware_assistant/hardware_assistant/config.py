"""
Configuration for Linux Hardware Q&A Assistant.
Defines security constraints, timeouts, allow-listed commands, and privilege models.
"""
import os
from typing import Dict, List
from pydantic_settings import BaseSettings

class HardwareAssistantSettings(BaseSettings):
    APP_NAME: str = "Linux Hardware Q&A Assistant"
    VERSION: str = "1.0.0"
    
    # Security & Execution Constraints
    SHELL_EXECUTION_ALLOWED: bool = False  # Strictly enforce shell=False
    COMMAND_TIMEOUT_SECONDS: int = 5
    MAX_OUTPUT_BYTES: int = 1024 * 512  # 512 KB stdout limit
    
    # Privilege Escalation Mode: "scoped_sudo", "daemon", "fallback"
    PRIVILEGE_MODE: str = os.getenv("HW_PRIVILEGE_MODE", "scoped_sudo")
    
    # System Execution Mode: "host" (executes on host OS) or "mock_linux" (virtualized Linux hardware)
    SYSTEM_MODE: str = os.getenv("HW_SYSTEM_MODE", "auto")

    # Anti-Hallucination Strictness
    STRICT_ANTI_HALLUCINATION: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"

hw_settings = HardwareAssistantSettings()

# STRICT ALLOW-LIST: Maps internal tool identifiers to fixed binary paths and allowed flags only
SAFE_COMMAND_ALLOWLIST: Dict[str, List[str]] = {
    "get_cpu_info": ["/usr/bin/lscpu"],
    "get_block_devices": ["/usr/bin/lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA,TRAN"],
    "get_memory_summary": ["/usr/bin/free", "-b"],
    "get_dmi_memory": ["/usr/sbin/dmidecode", "-t", "memory"],
    "get_pci_devices": ["/usr/bin/lspci", "-nnk"],
    "get_nvidia_gpu": ["/usr/bin/nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
    "read_proc_meminfo": ["/bin/cat", "/proc/meminfo"],
    "read_proc_cpuinfo": ["/bin/cat", "/proc/cpuinfo"]
}
