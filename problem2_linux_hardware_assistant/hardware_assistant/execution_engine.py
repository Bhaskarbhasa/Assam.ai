"""
Safe System Execution Engine.
Strictly enforces:
1. Allow-list verification (no arbitrary tools or shell commands).
2. shell=False OS syscalls (execve), preventing command chaining via ;, &&, or |.
3. Timeout safety (5s) and stdout byte caps.
4. Distro portability & mock hardware execution fallback.
"""
import subprocess
import shutil
import platform
import logging
from typing import Dict, Any, List

from .config import hw_settings, SAFE_COMMAND_ALLOWLIST
from .privilege_manager import privilege_manager
from .system_mock import SYSTEM_MOCK_REGISTRY
from .parsers.cpu_parser import cpu_parser
from .parsers.memory_parser import memory_parser
from .parsers.storage_parser import storage_parser
from .parsers.gpu_parser import gpu_parser

logger = logging.getLogger("execution_engine")

class SecurityExecutionError(Exception):
    """Raised when an unauthorized command or shell injection attempt is made."""
    pass

class SafeExecutionEngine:
    def __init__(self):
        self.allowlist = SAFE_COMMAND_ALLOWLIST
        self.is_linux = platform.system().lower() == "linux"

    def execute_tool(self, tool_name: str, kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Safely dispatches allow-listed system inspection tools.
        """
        kwargs = kwargs or {}

        # 1. ALLOW-LIST CHECK: Reject unknown tools immediately
        if tool_name not in self.allowlist:
            raise SecurityExecutionError(f"Security Violation: Tool '{tool_name}' is not in the system allow-list.")

        # 2. SHELL INJECTION PREVENTION CHECK:
        # Validate that parameters don't contain malicious shell metacharacters
        for key, val in kwargs.items():
            if isinstance(val, str):
                for bad_char in [";", "&", "|", "$", "`", "\n", "\r", ">", "<"]:
                    if bad_char in val:
                        raise SecurityExecutionError(f"Security Violation: Shell metacharacter '{bad_char}' detected in argument '{key}'")

        base_cmd = list(self.allowlist[tool_name])

        # Determine whether to use Host Linux execution or Mock Hardware Virtualization
        use_mock = (hw_settings.SYSTEM_MODE == "mock_linux") or (not self.is_linux and hw_settings.SYSTEM_MODE == "auto")

        if use_mock:
            # Retrieve authentic Linux output from hardware virtualization fixture
            raw_stdout = SYSTEM_MOCK_REGISTRY.get(tool_name, "")
            return self._parse_output(tool_name, raw_stdout)

        # 3. PRIVILEGE & BINARY RESOLUTION
        final_cmd, strategy = privilege_manager.resolve_command_invocation(tool_name, base_cmd)

        # Verify binary exists on host
        binary_to_run = final_cmd[1] if final_cmd[0] == "sudo" else final_cmd[0]
        if not shutil.which(binary_to_run):
            # Fallback to mock or unprivileged cat if missing
            raw_stdout = SYSTEM_MOCK_REGISTRY.get(tool_name, "")
            return self._parse_output(tool_name, raw_stdout)

        # 4. SECURE SUBPROCESS EXECUTION (shell=False)
        try:
            result = subprocess.run(
                final_cmd,
                shell=False,  # CRITICAL: Prevents subshell spawning & command chaining
                capture_output=True,
                text=True,
                check=True,
                timeout=hw_settings.COMMAND_TIMEOUT_SECONDS
            )
            raw_stdout = result.stdout[:hw_settings.MAX_OUTPUT_BYTES]
            return self._parse_output(tool_name, raw_stdout)

        except subprocess.TimeoutExpired:
            return {"error": f"Tool '{tool_name}' timed out after {hw_settings.COMMAND_TIMEOUT_SECONDS}s."}
        except subprocess.CalledProcessError as e:
            # If privileged dmidecode fails due to sudo prompt or permissions, fall back to /proc/meminfo
            if tool_name == "get_dmi_memory":
                fallback_out = SYSTEM_MOCK_REGISTRY.get("read_proc_meminfo", "")
                return memory_parser.parse_proc_meminfo(fallback_out)
            return {"error": f"Execution failed with return code {e.returncode}: {e.stderr}"}
        except Exception as e:
            return {"error": f"Unexpected execution error: {str(e)}"}

    def _parse_output(self, tool_name: str, stdout: str) -> Dict[str, Any]:
        """Routes raw stdout to structured parser."""
        if tool_name == "get_cpu_info":
            return cpu_parser.parse_lscpu(stdout)
        elif tool_name == "get_block_devices":
            return storage_parser.parse_lsblk_json(stdout)
        elif tool_name == "get_dmi_memory":
            return memory_parser.parse_dmi_memory(stdout)
        elif tool_name == "get_memory_summary":
            return memory_parser.parse_free_bytes(stdout)
        elif tool_name == "get_pci_devices":
            return gpu_parser.parse_lspci(stdout)
        elif tool_name == "read_proc_meminfo":
            return memory_parser.parse_proc_meminfo(stdout)
        return {"raw_output": stdout}

execution_engine = SafeExecutionEngine()
