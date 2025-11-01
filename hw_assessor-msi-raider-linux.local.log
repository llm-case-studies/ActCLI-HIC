# Hardware Assessment – msi-raider-linux.local

## System Summary
| Item | Value |
| --- | --- |
| Model | Raider GE78 HX 14VGG (Micro-Star International Co., Ltd.) |
| BIOS | E17S2IMS.70B |
| CPU | Intel(R) Core(TM) i9-14900HX |
| CPU Frequency | min 0.80 GHz, max 5.80 GHz |
| Cores / Threads | 24 / 32 |
| RAM Installed | approximately 29.1 GB across 2 module(s) |
| RAM Maximum (reported) | 64 GB |
| RAM Configured Speed | 5600 MT/s |
| RAM ECC | None |
| Virtualization | VT-x |
| Storage Devices Detected | 1 (NVMe: 1) |

## Memory Modules
| Slot | Size | Configured Speed | Part Number | Voltage |
| --- | --- | --- | --- | --- |
| Controller0-ChannelA-DIMM0 | 16 GB | 5600 MT/s | M425R2GA3BB0-CWMOD | 1.1 V |
| Controller1-ChannelA-DIMM0 | 16 GB | 5600 MT/s | M425R2GA3BB0-CWMOD | 1.1 V |

## Storage Devices
| Device | Model | Size | Type | Bus | Mountpoints |
| --- | --- | --- | --- | --- | --- |
| nvme0n1 | Micron_2400_MTFDKBA1T0QFM | 953.9G | SSD | NVME | /, /boot/efi, /home |

**Storage Slot Insight:** MSI documentation indicates two M.2 NVMe slots (PCIe Gen5 x4 primary, PCIe Gen4 x4 secondary). Detected 1/2 NVMe slots populated; about 1 slot(s) likely free.

## GPU
Detected PCI/PCIe display adapters:
- 0000:00:02.0 VGA compatible controller: Intel Corporation Raptor Lake-S UHD Graphics (rev 04)
- 0000:01:00.0 VGA compatible controller: NVIDIA Corporation AD106M [GeForce RTX 4070 Max-Q / Mobile] (rev a1)

| NVIDIA GPU | Reported VRAM |
| --- | --- |
| NVIDIA GeForce RTX 4070 Laptop GPU | 8188 MiB |

## Role Suitability
| Role | Rating | Notes |
| --- | --- | --- |
| Developer workstation | Good | Solid balance; consider RAM or NVMe upgrades if workloads grow. |
| Developer server | Not ideal | Upgrade RAM/CPU or offload heavier services.<br>Virtualization extensions detected (VT-x).<br>Specs under typical server thresholds; keep workloads light. |
| LLM / ML | Limited | Add a higher-VRAM GPU or use cloud resources for serious ML.<br>GPU VRAM is minimal for ML; expect CPU-bound inference. |
| Media / streaming | Good | Discrete GPU should accelerate encoding and multiple streams. |
| NAS / DB | Limited | Expand storage and consider ECC memory for reliability.<br>Only one storage device detected; add more drives for redundancy and performance. |

## Upgrade Opportunities
- Replace existing SODIMMs to move toward the 64 GB platform ceiling.
- Only one storage device detected; add another NVMe/SATA drive for capacity or redundancy.
- Use the free M.2 slot for a second NVMe SSD if additional fast storage is needed.

## Command Notes
- Run with sudo so dmidecode can read SMBIOS tables.
- Install optional tools (nvme-cli, nvidia-smi) for fuller reports.
- For macOS hosts, use system_profiler/ioreg equivalents instead; this script targets Linux.

