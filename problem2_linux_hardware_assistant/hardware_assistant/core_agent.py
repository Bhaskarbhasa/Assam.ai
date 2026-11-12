"""
Core Agent Orchestration Engine.
Coordinates:
1. Natural Language Intent Recognition & Safe Tool Selection
2. Secure Execution via Allow-Listed Engine
3. Multi-Turn Follow-Up Resolution with Context Buffer
4. Strict Anti-Hallucination Answer Synthesis (solely grounded in verified JSON)
"""
import re
from typing import Dict, Any, Tuple, Optional
from .execution_engine import execution_engine, SecurityExecutionError
from .memory_context import session_context, ConversationSession
from .config import hw_settings

SYSTEM_PROMPT = """You are a Linux Hardware Inspection Assistant running locally on the user's laptop.
STRICT OPERATING CONSTRAINTS:
1. Base your response solely on the provided verified JSON hardware data.
2. If the JSON does not contain the answer, state: 'I cannot determine this hardware detail from system data.'
3. Never guess, assume, or hallucinate clock speeds, maximum capacity, or slot counts.
4. Explain technical metrics (NVMe vs SATA, DDR generation, PCIe lanes) clearly and concisely.
"""

class HardwareQAAgent:
    def __init__(self, session: Optional[ConversationSession] = None):
        self.session = session or session_context

    def detect_tool_intent(self, user_query: str) -> Tuple[Optional[str], str]:
        """
        Maps natural language query to an allow-listed tool identifier.
        Supports multi-turn context checking for follow-up questions.
        """
        q = user_query.lower()

        # Follow-up detection (e.g. "and what about the GPU?", "how many slots are free?")
        if "gpu" in q or "graphics" in q or "video card" in q or "display controller" in q or "vga" in q or "nvidia" in q:
            return "get_pci_devices", "gpu"

        if "ram" in q or "memory" in q or "ddr" in q or "upgrade" in q or "dimm" in q or "slots" in q:
            return "get_dmi_memory", "memory"

        if "ssd" in q or "nvme" in q or "hard disk" in q or "hdd" in q or "drive" in q or "storage" in q or "disk" in q:
            return "get_block_devices", "storage"

        if "cpu" in q or "processor" in q or "core" in q or "thread" in q or "cache" in q or "hz" in q:
            return "get_cpu_info", "cpu"

        # General summary if generic question
        if "hardware" in q or "specs" in q or "system" in q:
            return "get_cpu_info", "cpu"

        return None, "unknown"

    def synthesize_answer(self, query: str, category: str, data: Dict[str, Any]) -> str:
        """
        Synthesizes an accurate, concise natural language answer grounded exclusively in the normalized JSON.
        """
        q = query.lower()

        if "error" in data:
            return f"Unable to complete system inspection: {data['error']}"

        # --- MEMORY / RAM SYNTHESIS ---
        if category == "memory":
            if data.get("fallback_mode") == "non_root_proc_meminfo":
                return (
                    f"You have approximately {data.get('total_installed_gb')} GB of RAM installed "
                    f"({data.get('available_gb')} GB currently available). "
                    f"Note: Detailed slot topology and maximum board capacity require root privileges (dmidecode)."
                )

            installed_gb = data.get("installed_total_gb", 0)
            max_gb = data.get("maximum_board_capacity_gb")
            total_slots = data.get("total_slots", 0)
            used_slots = data.get("used_slots", 0)
            free_slots = data.get("free_slots", 0)
            rec = data.get("recommendation", "")

            # Check specific slot inquiry
            if "slot" in q and ("how many" in q or "free" in q or "empty" in q):
                return f"You have {total_slots} memory slots in total: {used_slots} used and {free_slots} free."

            if "upgrade" in q or "add" in q or "more" in q or "how much" in q:
                if rec:
                    return rec
                return f"You currently have {installed_gb} GB installed across {used_slots} of {total_slots} slots."

            # General RAM capacity
            slots_detail = []
            for s in data.get("slots", []):
                if s["status"] == "Installed":
                    slots_detail.append(f"{s['slot']}: {s.get('size')} ({s.get('type')}, {s.get('speed')})")
            
            detail_str = "; ".join(slots_detail) if slots_detail else ""
            return (
                f"You have {installed_gb} GB RAM installed in {used_slots} of {total_slots} slots "
                f"({free_slots} empty slot). Maximum motherboard capacity is {max_gb or 'Unknown'} GB. "
                f"Installed modules: {detail_str}."
            )

        # --- STORAGE / SSD / NVME SYNTHESIS ---
        elif category == "storage":
            drives = data.get("drives", [])
            if not drives:
                return "I cannot determine this hardware detail from system data: No block devices detected."

            # Check NVMe specific inquiry
            if "nvme" in q:
                nvme_drives = [d for d in drives if d.get("is_nvme")]
                if nvme_drives:
                    first = nvme_drives[0]
                    return f"Yes, your drive {first['device_name']} ({first['model']}, {first['capacity']}) is an NVMe SSD utilizing high-speed PCIe transport (ROTA=0, TRAN={first['transport_protocol']})."
                else:
                    return "No, none of the detected storage drives are NVMe devices."

            # General storage inquiry
            lines = []
            for d in drives:
                lines.append(f"• {d['device_name']}: {d['model']} ({d['capacity']}) - {d['drive_technology']}")
            return "Detected Storage Devices:\n" + "\n".join(lines)

        # --- GPU / GRAPHICS SYNTHESIS ---
        elif category == "gpu":
            gpus = data.get("gpus", [])
            if not gpus:
                return "I cannot determine this hardware detail from system data: No VGA or display controllers identified."

            parts = []
            for g in gpus:
                parts.append(
                    f"{g['vendor']} {g.get('raw_device_description', '').split(':')[-1].strip()} "
                    f"({g['gpu_type']}, kernel driver: {g['kernel_driver']})"
                )
            return "Installed Graphics Hardware:\n• " + "\n• ".join(parts)

        # --- CPU SYNTHESIS ---
        elif category == "cpu":
            model = data.get("model_name", "Unknown")
            arch = data.get("architecture", "Unknown")
            cores = data.get("physical_cores", 1)
            cpus = data.get("total_logical_cpus", 1)
            max_mhz = data.get("max_frequency_mhz", "Unknown")
            virt = data.get("virtualization_support", "None")

            if "core" in q or "thread" in q:
                return f"Your CPU has {cores} physical cores and {cpus} logical threads ({data.get('threads_per_core', 1)} threads per core)."

            return (
                f"Processor: {model} ({arch})\n"
                f"Cores/Threads: {cores} physical cores, {cpus} logical threads\n"
                f"Max Frequency: {max_mhz} MHz\n"
                f"Hardware Virtualization: {virt}"
            )

        return "I cannot determine this hardware detail from system data."

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        End-to-end question processing loop with security sandboxing,
        caching, and answer generation.
        """
        self.session.add_user_message(user_query)

        # 1. Identify Intent & Map to Allow-Listed Tool
        tool_name, category = self.detect_tool_intent(user_query)

        if not tool_name:
            reply = "I cannot determine this hardware detail from system data. I can inspect CPU, Memory topology, Storage/NVMe drives, and GPU controllers."
            self.session.add_assistant_message(reply, tool_used=None)
            return {
                "answer": reply,
                "tool_called": None,
                "category": None,
                "structured_data": {}
            }

        # 2. Check if already in cache and user query is a simple follow-up
        cached = self.session.get_cached_spec(category)
        if cached and not ("refresh" in user_query.lower() or "check again" in user_query.lower()):
            structured_data = cached
            tool_executed = f"{tool_name} (cached)"
        else:
            # 3. Secure Execution via Allow-Listed Engine
            try:
                structured_data = execution_engine.execute_tool(tool_name)
                self.session.update_hardware_cache(category, structured_data)
                tool_executed = tool_name
            except SecurityExecutionError as e:
                reply = f"Security Enforcement Alert: {str(e)}"
                self.session.add_assistant_message(reply, tool_used=tool_name)
                return {
                    "answer": reply,
                    "tool_called": tool_name,
                    "category": category,
                    "structured_data": {"security_violation": str(e)}
                }

        # 4. Contextual Answer Synthesis strictly grounded in JSON
        answer = self.synthesize_answer(user_query, category, structured_data)
        self.session.add_assistant_message(answer, tool_used=tool_executed)

        return {
            "answer": answer,
            "tool_called": tool_executed,
            "category": category,
            "structured_data": structured_data
        }

hardware_agent = HardwareQAAgent()
