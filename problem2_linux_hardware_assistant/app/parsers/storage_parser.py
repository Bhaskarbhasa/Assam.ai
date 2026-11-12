"""
Parser for Block Devices and Storage (lsblk -J).
Normalizes disk drives, transport protocols (NVMe vs SATA),
rotational status (SSD vs HDD), partitions, and mountpoints.
"""
import json
from typing import Dict, Any, List

class StorageParser:
    def parse_lsblk_json(self, stdout: str) -> Dict[str, Any]:
        """
        Parses `lsblk -J -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA,TRAN` JSON output.
        """
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return {"error": "Failed to decode lsblk JSON output"}

        devices_raw = data.get("blockdevices", [])
        disks: List[Dict[str, Any]] = []

        for dev in devices_raw:
            dev_type = dev.get("type", "").lower()
            name = dev.get("name", "")
            size = dev.get("size", "")
            model = (dev.get("model") or "Generic Drive").strip()
            rota = dev.get("rota", False) # True/1 for HDD, False/0 for SSD
            tran = (dev.get("tran") or "").lower() # nvme, sata, usb
            mountpoint = dev.get("mountpoint")

            is_ssd = not rota
            is_nvme = "nvme" in tran or "nvme" in name.lower()

            drive_tech = "NVMe SSD" if is_nvme else ("SATA SSD" if is_ssd else "Rotational HDD")

            # Extract partitions
            children = dev.get("children", [])
            partitions = []
            for child in children:
                partitions.append({
                    "name": child.get("name"),
                    "size": child.get("size"),
                    "mountpoint": child.get("mountpoint")
                })

            disks.append({
                "device_name": name,
                "model": model,
                "capacity": size,
                "drive_technology": drive_tech,
                "is_ssd": is_ssd,
                "is_nvme": is_nvme,
                "transport_protocol": tran or ("nvme" if is_nvme else "unknown"),
                "mountpoint": mountpoint,
                "partitions": partitions
            })

        return {
            "total_drives": len(disks),
            "drives": disks
        }

storage_parser = StorageParser()
