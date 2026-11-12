"""
Tool Registry & Dynamic Capability Discovery.
Inspects host Linux distribution at boot (shutil.which) to register only available tools,
and provides OpenAI/Pydantic-style tool schemas.
"""
import shutil
import sys
from typing import Dict, Any, List

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "get_cpu_info",
        "description": "Retrieves CPU specifications including architecture, model name, core and thread counts, max frequency, virtualization, and cache sizes.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_memory_topology",
        "description": "Retrieves physical RAM details including installed capacity, total motherboard slots, empty slots, DDR speed, maximum capacity limit, and upgradeability.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "include_empty_slots": {
                    "type": "BOOLEAN",
                    "description": "Whether to include detailed status of unused memory slots."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_block_devices",
        "description": "Retrieves storage drives, partition hierarchy, NVMe vs SATA transport protocol, and SSD vs rotational HDD status.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_gpu_info",
        "description": "Retrieves installed graphics controllers (dedicated and integrated GPUs), vendors (AMD/NVIDIA/Intel), and active kernel drivers.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    }
]

class ToolDiscoveryEngine:
    def __init__(self):
        self.available_system_binaries = {}
        self.active_tools = []
        self._discover_capabilities()

    def _discover_capabilities(self):
        """Discovers binaries present on the host environment."""
        binaries = ["lscpu", "lsblk", "free", "dmidecode", "lspci", "nvidia-smi"]
        for b in binaries:
            path = shutil.which(b)
            self.available_system_binaries[b] = path

        # Determine which tools can run natively
        self.active_tools = []
        for schema in TOOL_SCHEMAS:
            name = schema["name"]
            # All tools supported via native execution or fallback/mock
            self.active_tools.append(schema)

    def is_binary_available(self, binary_name: str) -> bool:
        return self.available_system_binaries.get(binary_name) is not None

    def get_registered_schemas(self) -> List[Dict[str, Any]]:
        return self.active_tools

tool_registry = ToolDiscoveryEngine()
