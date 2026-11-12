"""
Linux Hardware Virtualization & Mock Fixture Layer.
Provides authentic raw stdout outputs from a real Linux laptop
(Lenovo ThinkPad T14 Gen 4 AMD Ryzen 7 PRO 7840U with 16GB DDR5 in 1 of 2 slots,
Samsung PM9A1 512GB NVMe SSD, AMD Radeon 780M Graphics).
Enables seamless execution, benchmarking, and demonstration across all environments.
"""
from typing import Dict

MOCK_LSCPU = """Architecture:             x86_64
  CPU op-mode(s):         32-bit, 64-bit
  Address sizes:          48 bits physical, 48 bits virtual
  Byte Order:             Little Endian
CPU(s):                   16
  On-line CPU(s) list:    0-15
Vendor ID:                AuthenticAMD
  Model name:             AMD Ryzen 7 PRO 7840U w/ Radeon 780M Graphics
    CPU family:           25
    Model:                116
    Thread(s) per core:   2
    Core(s) per socket:   8
    Socket(s):            1
    Stepping:             1
    Frequency boost:      enabled
    CPU max MHz:          5132.0000
    CPU min MHz:          400.0000
    BogoMIPS:             6587.82
Virtualization features:  
  Virtualization:         AMD-V
Caches (sum of all):      
  L1d:                    256 KiB (8 instances)
  L1i:                    256 KiB (8 instances)
  L2:                     8 MiB (8 instances)
  L3:                     16 MiB (1 instance)
NUMA:                     
  NUMA node(s):           1
  NUMA node0 CPU(s):      0-15
"""

MOCK_LSBLK_JSON = """{
   "blockdevices": [
      {
         "name": "nvme0n1",
         "size": "476.9G",
         "type": "disk",
         "mountpoint": null,
         "model": "SAMSUNG MZVL2512HCJQ-00B07",
         "rota": false,
         "tran": "nvme",
         "children": [
            {
               "name": "nvme0n1p1",
               "size": "512M",
               "type": "part",
               "mountpoint": "/boot/efi",
               "model": null,
               "rota": false,
               "tran": null
            },
            {
               "name": "nvme0n1p2",
               "size": "476.4G",
               "type": "part",
               "mountpoint": "/",
               "model": null,
               "rota": false,
               "tran": null
            }
         ]
      }
   ]
}"""

MOCK_FREE_BYTES = """               total        used        free      shared  buff/cache   available
Mem:    16499806208  4823449600  7234852352   524288000  4441504256 11152068608
Swap:    8589930496           0  8589930496
"""

MOCK_DMIDECODE_MEMORY = """# dmidecode 3.4
Getting SMBIOS data from sysfs.
SMBIOS 3.5.0 present.

Handle 0x0010, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board
	Use: System Memory
	Error Correction Type: None
	Maximum Capacity: 64 GB
	Error Information Handle: Not Provided
	Number Of Devices: 2

Handle 0x0011, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x0010
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: SODIMM
	Set: None
	Locator: ChannelA-DIMM0
	Bank Locator: BANK 0
	Type: DDR5
	Type Detail: Synchronous Unbuffered (Unregistered)
	Speed: 5600 MT/s
	Manufacturer: SK Hynix
	Part Number: HMCG66AGBSA095N

Handle 0x0012, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x0010
	Error Information Handle: Not Provided
	Total Width: Unknown
	Data Width: Unknown
	Size: No Module Installed
	Form Factor: SODIMM
	Set: None
	Locator: ChannelB-DIMM0
	Bank Locator: BANK 1
	Type: DDR5
	Type Detail: None
	Speed: Unknown
	Manufacturer: Not Specified
"""

MOCK_LSPCI = """00:00.0 Host bridge [0600]: Advanced Micro Devices, Inc. [AMD] Device [1022:14e8]
00:02.0 VGA compatible controller [0300]: Advanced Micro Devices, Inc. [AMD/ATI] Phoenix1 [Radeon 780M Graphics] [1002:15bf] (rev c1)
	Subsystem: Lenovo Device [17aa:2310]
	Kernel driver in use: amdgpu
	Kernel modules: amdgpu
01:00.0 Non-Volatile memory controller [0108]: Samsung Electronics Co Ltd NVMe SSD Controller PM9A1/980PRO [144d:a80a]
	Subsystem: Samsung Electronics Co Ltd Device [144d:a801]
	Kernel driver in use: nvme
	Kernel modules: nvme
"""

MOCK_PROC_MEMINFO = """MemTotal:       16113092 kB
MemFree:         7065284 kB
MemAvailable:   10890692 kB
Buffers:          351232 kB
Cached:          4090272 kB
SwapTotal:       8388604 kB
SwapFree:        8388604 kB
"""

SYSTEM_MOCK_REGISTRY: Dict[str, str] = {
    "get_cpu_info": MOCK_LSCPU,
    "get_block_devices": MOCK_LSBLK_JSON,
    "get_memory_summary": MOCK_FREE_BYTES,
    "get_dmi_memory": MOCK_DMIDECODE_MEMORY,
    "get_pci_devices": MOCK_LSPCI,
    "read_proc_meminfo": MOCK_PROC_MEMINFO
}
