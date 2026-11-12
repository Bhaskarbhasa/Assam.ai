"""
Parser for Linux CPU information (lscpu & /proc/cpuinfo).
Transforms raw key-value text into validated, structured JSON.
"""
import re
from typing import Dict, Any

class CPUParser:
    def parse_lscpu(self, stdout: str) -> Dict[str, Any]:
        """
        Parses `lscpu` stdout into normalized dictionary.
        """
        raw_map = {}
        for line in stdout.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                raw_map[key.strip()] = val.strip()

        # Extract normalized fields
        model_name = raw_map.get("Model name", raw_map.get("Processor", "Unknown"))
        architecture = raw_map.get("Architecture", "Unknown")
        cores_per_socket = raw_map.get("Core(s) per socket", "1")
        threads_per_core = raw_map.get("Thread(s) per core", "1")
        sockets = raw_map.get("Socket(s)", "1")
        total_cpus = raw_map.get("CPU(s)", "1")
        max_mhz = raw_map.get("CPU max MHz", raw_map.get("CPU MHz", "Unknown"))
        virtualization = raw_map.get("Virtualization", raw_map.get("Hypervisor vendor", "None"))
        
        # Caches (support both 'L3 cache' and newer 'L3')
        l1d = raw_map.get("L1d", raw_map.get("L1d cache", "Unknown"))
        l1i = raw_map.get("L1i", raw_map.get("L1i cache", "Unknown"))
        l2 = raw_map.get("L2", raw_map.get("L2 cache", "Unknown"))
        l3 = raw_map.get("L3", raw_map.get("L3 cache", "Unknown"))

        return {
            "model_name": model_name,
            "architecture": architecture,
            "total_logical_cpus": int(total_cpus) if total_cpus.isdigit() else 1,
            "physical_cores": int(cores_per_socket) * int(sockets) if cores_per_socket.isdigit() and sockets.isdigit() else 1,
            "threads_per_core": int(threads_per_core) if threads_per_core.isdigit() else 1,
            "sockets": int(sockets) if sockets.isdigit() else 1,
            "max_frequency_mhz": max_mhz,
            "virtualization_support": virtualization,
            "caches": {
                "l1d": l1d,
                "l1i": l1i,
                "l2": l2,
                "l3": l3
            }
        }

cpu_parser = CPUParser()
