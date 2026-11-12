"""
Unit Tests for Command Output Parsers and Normalizers.
"""
from hardware_assistant.parsers.cpu_parser import cpu_parser
from hardware_assistant.parsers.memory_parser import memory_parser
from hardware_assistant.parsers.storage_parser import storage_parser
from hardware_assistant.parsers.gpu_parser import gpu_parser
from hardware_assistant.system_mock import MOCK_LSCPU, MOCK_LSBLK_JSON, MOCK_DMIDECODE_MEMORY, MOCK_PROC_MEMINFO, MOCK_LSPCI

def test_cpu_parser_lscpu():
    parsed = cpu_parser.parse_lscpu(MOCK_LSCPU)
    assert parsed["architecture"] == "x86_64"
    assert "AMD Ryzen 7 PRO 7840U" in parsed["model_name"]
    assert parsed["total_logical_cpus"] == 16
    assert parsed["physical_cores"] == 8
    assert parsed["virtualization_support"] == "AMD-V"
    assert "16 MiB" in parsed["caches"]["l3"]

def test_memory_parser_dmi():
    parsed = memory_parser.parse_dmi_memory(MOCK_DMIDECODE_MEMORY)
    assert parsed["maximum_board_capacity_gb"] == 64
    assert parsed["total_slots"] == 2
    assert parsed["used_slots"] == 1
    assert parsed["free_slots"] == 1
    assert parsed["installed_total_gb"] == 16
    assert parsed["can_upgrade"] is True
    assert "You have 16 GB installed in 1 of 2 slots" in parsed["recommendation"]

def test_memory_parser_non_root_fallback():
    parsed = memory_parser.parse_proc_meminfo(MOCK_PROC_MEMINFO)
    assert parsed["fallback_mode"] == "non_root_proc_meminfo"
    assert parsed["total_installed_gb"] > 15.0
    assert "Root privileges" in parsed["note"]

def test_storage_parser_lsblk():
    parsed = storage_parser.parse_lsblk_json(MOCK_LSBLK_JSON)
    assert parsed["total_drives"] == 1
    drive = parsed["drives"][0]
    assert drive["device_name"] == "nvme0n1"
    assert drive["is_nvme"] is True
    assert drive["is_ssd"] is True
    assert drive["transport_protocol"] == "nvme"
    assert len(drive["partitions"]) == 2

def test_gpu_parser_lspci():
    parsed = gpu_parser.parse_lspci(MOCK_LSPCI)
    assert parsed["total_gpus_detected"] == 1
    gpu = parsed["gpus"][0]
    assert gpu["vendor"] == "AMD"
    assert "Radeon 780M" in gpu["raw_device_description"]
    assert gpu["kernel_driver"] == "amdgpu"
