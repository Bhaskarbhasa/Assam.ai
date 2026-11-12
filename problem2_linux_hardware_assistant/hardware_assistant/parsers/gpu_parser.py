"""
Parser for GPU / Graphics hardware (lspci -nnk and nvidia-smi).
Extracts GPU controller, vendor, integrated vs discrete type, and kernel driver.
"""
import re
from typing import Dict, Any, List

class GPUParser:
    def parse_lspci(self, stdout: str) -> Dict[str, Any]:
        """
        Parses `lspci -nnk` output for VGA and 3D display controllers.
        """
        controllers: List[Dict[str, Any]] = []
        
        # Split by PCI slot blocks (e.g. "00:02.0 ...")
        blocks = re.split(r"\n(?=[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F])", stdout)
        
        for block in blocks:
            if "VGA compatible controller" in block or "3D controller" in block or "Display controller" in block:
                lines = block.strip().splitlines()
                header = lines[0] if lines else ""
                
                # Extract vendor and device name
                # Example: 05:00.0 VGA compatible controller [0300]: Advanced Micro Devices, Inc. [AMD/ATI] Cezanne [Radeon Vega Series / Radeon Vega Mobile Series] [1002:1638] (rev c5)
                # Or NVIDIA Corporation AD106M [GeForce RTX 4070 Max-Q / Mobile]
                driver = "Unknown"
                kernel_modules = []
                for line in lines[1:]:
                    if "Kernel driver in use:" in line:
                        driver = line.split(":", 1)[1].strip()
                    elif "Kernel modules:" in line:
                        kernel_modules = [m.strip() for m in line.split(":", 1)[1].split(",")]

                vendor = "Unknown"
                if "NVIDIA" in header.upper():
                    vendor = "NVIDIA"
                elif "AMD" in header.upper() or "ATI" in header.upper():
                    vendor = "AMD"
                elif "INTEL" in header.upper():
                    vendor = "Intel"

                is_dedicated = "3D controller" in header or ("NVIDIA" in vendor and "GeForce" in header)
                gpu_type = "Dedicated / Discrete GPU" if is_dedicated else "Integrated GPU (iGPU)"

                controllers.append({
                    "pci_identifier": header.split()[0] if header else "",
                    "raw_device_description": header,
                    "vendor": vendor,
                    "gpu_type": gpu_type,
                    "kernel_driver": driver,
                    "kernel_modules": kernel_modules
                })

        return {
            "total_gpus_detected": len(controllers),
            "gpus": controllers
        }

    def parse_nvidia_smi(self, stdout: str) -> Dict[str, Any]:
        """
        Parses CSV output from nvidia-smi query.
        """
        lines = [l.strip() for l in stdout.strip().splitlines() if l.strip()]
        if not lines:
            return {"nvidia_gpu_detected": False}

        gpus = []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                gpus.append({
                    "model": parts[0],
                    "total_memory_mb": parts[1],
                    "driver_version": parts[2]
                })

        return {
            "nvidia_gpu_detected": True,
            "discrete_gpus": gpus
        }

gpu_parser = GPUParser()
