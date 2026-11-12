"""
Privilege Escalation & Security Strategy Manager.
Safely manages root vs unprivileged execution for sensitive hardware inspection tools (e.g. dmidecode).
Supports 3 production strategies:
1. Scoped Sudoers (/etc/sudoers.d/hw-assistant)
2. Background Privilege Daemon (abstracted IPC)
3. Non-Root Fallback (/proc, /sys, lscpu, free)
"""
import os
import shutil
import subprocess
import logging
from typing import Tuple, List, Optional
from .config import hw_settings

logger = logging.getLogger("privilege_manager")

SUDOERS_SAMPLE_CONFIG = """# Place in /etc/sudoers.d/hw-assistant
# Grants minimal scoped execution for hardware inspection only
%hwassistant ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode -t memory, /usr/sbin/dmidecode -t bios
"""

class PrivilegeManager:
    def __init__(self, mode: str = hw_settings.PRIVILEGE_MODE):
        self.mode = mode  # "scoped_sudo", "daemon", "fallback"

    def can_run_sudo_tool(self, tool_binary: str) -> bool:
        """
        Tests whether the current user can execute the specified binary via sudo without prompting for a password.
        """
        # Quick non-interactive sudo dry run (-n = non-interactive)
        if not shutil.which("sudo"):
            return False
            
        try:
            res = subprocess.run(
                ["sudo", "-n", tool_binary, "-t", "memory"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return res.returncode == 0
        except Exception:
            return False

    def resolve_command_invocation(self, tool_name: str, base_cmd: List[str]) -> Tuple[List[str], str]:
        """
        Determines the exact execution vector for a tool depending on privileges.
        Returns:
            cmd (List[str]): Fixed command array for execve (shell=False)
            strategy_used (str): "scoped_sudo", "daemon", or "unprivileged_fallback"
        """
        # If tool requires root (e.g. dmidecode)
        if tool_name == "get_dmi_memory":
            if self.mode == "scoped_sudo":
                # Prepend sudo safely
                return ["sudo", "-n"] + base_cmd, "scoped_sudo"
            elif self.mode == "daemon":
                # Privilege Daemon Mode: simulates or calls local IPC daemon
                return base_cmd, "privilege_daemon_ipc"
            else:
                # Fallback mode: query /proc/meminfo instead
                return ["/bin/cat", "/proc/meminfo"], "unprivileged_fallback"

        # Standard unprivileged commands (lscpu, lsblk, free, lspci)
        return base_cmd, "unprivileged_direct"

privilege_manager = PrivilegeManager()
