"""
Parser for Memory (RAM) topology.
Parses both unprivileged (`free -b`, `/proc/meminfo`) and privileged (`dmidecode -t memory`) outputs.
Computes upgradeability, empty slots, and maximum capacity.
"""
import re
from typing import Dict, Any, List

class MemoryParser:
    def parse_free_bytes(self, stdout: str) -> Dict[str, Any]:
        """
        Parses `free -b` stdout.
        """
        lines = stdout.strip().splitlines()
        if len(lines) < 2:
            return {"error": "Invalid free output"}

        # Typically:
        #               total        used        free      shared  buff/cache   available
        # Mem:    16499806208  4823449600  8234852352   524288000  3441504256 11152068608
        mem_line = lines[1].split()
        if len(mem_line) >= 7 and "Mem:" in mem_line[0]:
            total_bytes = int(mem_line[1])
            used_bytes = int(mem_line[2])
            free_bytes = int(mem_line[3])
            available_bytes = int(mem_line[6])
            
            total_gb = round(total_bytes / (1024 ** 3), 2)
            used_gb = round(used_bytes / (1024 ** 3), 2)
            available_gb = round(available_bytes / (1024 ** 3), 2)

            return {
                "total_installed_bytes": total_bytes,
                "total_installed_gb": total_gb,
                "used_gb": used_gb,
                "available_gb": available_gb
            }
        return {"raw_output": stdout}

    def parse_dmi_memory(self, stdout: str) -> Dict[str, Any]:
        """
        Parses `dmidecode -t memory` stdout for physical topology, slots, and max board limit.
        """
        # Maximum Capacity
        max_cap_match = re.search(r"Maximum Capacity:\s*([0-9]+)\s*([GMK]B)", stdout, re.IGNORECASE)
        max_capacity_str = f"{max_cap_match.group(1)} {max_cap_match.group(2)}" if max_cap_match else "Unknown"
        max_capacity_gb = int(max_cap_match.group(1)) if max_cap_match and "G" in max_cap_match.group(2).upper() else None

        # Slots breakdown
        # Split by "Memory Device"
        devices = stdout.split("Memory Device")
        slots: List[Dict[str, Any]] = []
        installed_count = 0
        empty_count = 0
        installed_total_gb = 0

        for dev in devices[1:]:
            size_match = re.search(r"Size:\s*([^\n\r]+)", dev)
            locator_match = re.search(r"Locator:\s*([^\n\r]+)", dev)
            type_match = re.search(r"Type:\s*([^\n\r]+)", dev)
            speed_match = re.search(r"Speed:\s*([^\n\r]+)", dev)

            size_str = size_match.group(1).strip() if size_match else "Unknown"
            locator = locator_match.group(1).strip() if locator_match else "Unknown"
            mem_type = type_match.group(1).strip() if type_match else "Unknown"
            speed = speed_match.group(1).strip() if speed_match else "Unknown"

            is_empty = "No Module Installed" in size_str or size_str == "None" or "0" in size_str

            if is_empty:
                empty_count += 1
                slots.append({
                    "slot": locator,
                    "status": "Empty",
                    "installed_module": None
                })
            else:
                installed_count += 1
                gb_match = re.search(r"([0-9]+)\s*GB", size_str, re.IGNORECASE)
                if gb_match:
                    installed_total_gb += int(gb_match.group(1))

                slots.append({
                    "slot": locator,
                    "status": "Installed",
                    "size": size_str,
                    "type": mem_type,
                    "speed": speed
                })

        total_slots = len(slots)

        # Upgrade Recommendation Engine
        can_upgrade = False
        upgrade_headroom_gb = None
        recommendation = ""

        if max_capacity_gb and installed_total_gb:
            upgrade_headroom_gb = max_capacity_gb - installed_total_gb
            if empty_count > 0 and upgrade_headroom_gb > 0:
                can_upgrade = True
                max_stick_size = min(upgrade_headroom_gb, 32)
                recommendation = f"You have {installed_total_gb} GB installed in {installed_count} of {total_slots} slots. The motherboard supports up to {max_capacity_gb} GB, and you have {empty_count} empty slot(s). You can add a module of up to {max_stick_size} GB."
            elif empty_count == 0 and upgrade_headroom_gb > 0:
                can_upgrade = True
                recommendation = f"All {total_slots} slots are occupied, but board supports up to {max_capacity_gb} GB. You can upgrade by replacing existing modules."
            else:
                recommendation = f"System is currently maxed out at {installed_total_gb} GB."

        return {
            "maximum_board_capacity_gb": max_capacity_gb,
            "maximum_capacity_str": max_capacity_str,
            "total_slots": total_slots,
            "used_slots": installed_count,
            "free_slots": empty_count,
            "installed_total_gb": installed_total_gb,
            "slots": slots,
            "can_upgrade": can_upgrade,
            "upgrade_headroom_gb": upgrade_headroom_gb,
            "recommendation": recommendation
        }

    def parse_proc_meminfo(self, stdout: str) -> Dict[str, Any]:
        """
        Unprivileged fallback parsing /proc/meminfo.
        """
        fields = {}
        for line in stdout.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()

        mem_total = fields.get("MemTotal", "0 kB")
        mem_avail = fields.get("MemAvailable", "0 kB")

        total_kb = int(re.search(r"(\d+)", mem_total).group(1)) if re.search(r"(\d+)", mem_total) else 0
        avail_kb = int(re.search(r"(\d+)", mem_avail).group(1)) if re.search(r"(\d+)", mem_avail) else 0

        total_gb = round(total_kb / (1024 * 1024), 2)
        avail_gb = round(avail_kb / (1024 * 1024), 2)

        return {
            "fallback_mode": "non_root_proc_meminfo",
            "total_installed_gb": total_gb,
            "available_gb": avail_gb,
            "note": "Root privileges (dmidecode) required to inspect physical motherboard slots and maximum upgrade limit."
        }

memory_parser = MemoryParser()
