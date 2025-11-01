#!/usr/bin/env python3
"""
Hardware capability assessor that produces a Markdown report.

Requires standard Linux tooling (dmidecode, lscpu, lsblk, lspci, free).
Optional utilities (nvme, nvidia-smi) enrich the output when present.
"""

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from getpass import getpass
from typing import Sequence

STORAGE_HINTS = {
    "Raider GE78 HX 14VGG": {
        "nvme_slots": 2,
        "notes": "MSI documentation indicates two M.2 NVMe slots (PCIe Gen5 x4 primary, PCIe Gen4 x4 secondary)."
    },
    "Raider GE78": {
        "nvme_slots": 2,
        "notes": "GE78 chassis typically offers two M.2 NVMe slots; confirm in the service manual for your exact sub-model."
    }
}


@dataclass
class CommandResult:
    cmd: Sequence[str]
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    timed_out: bool = False
    error: str | None = None
    duration: float | None = None

    @property
    def success(self) -> bool:
        return not self.error and not self.timed_out and (self.returncode in (0, None))


_COMMAND_LOG: list[CommandResult] = []


@dataclass
class PrivilegeState:
    is_root: bool = False
    use_sudo: bool = False
    requires_password: bool = False
    password: str | None = None
    mode: str = "auto"
    configured: bool = False


_PRIV_STATE = PrivilegeState(is_root=(os.geteuid() == 0))
_WARNED_MISSING_SUDO = False


def _sudo_check_noninteractive(timeout: float = 3.0) -> bool:
    """Return True if sudo can be invoked non-interactively."""

    try:
        proc = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0


def _sudo_validate_password(password: str, timeout: float = 5.0) -> bool:
    """Validate a sudo password by attempting `sudo -S -v`."""

    try:
        proc = subprocess.run(
            ["sudo", "-S", "-v"],
            input=f"{password}\n",
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0


def configure_privileges(mode: str = "auto", prompt_password: bool = False) -> PrivilegeState:
    """Determine whether sudo should be used for privileged commands."""

    mode = mode.lower()
    if mode not in {"auto", "skip", "require"}:
        raise ValueError(f"Invalid sudo mode: {mode}")

    state = _PRIV_STATE
    state.mode = mode
    state.is_root = os.geteuid() == 0
    state.configured = True
    state.use_sudo = False
    state.requires_password = False
    state.password = None

    if state.is_root:
        return state

    if mode == "skip":
        return state

    if _sudo_check_noninteractive():
        state.use_sudo = True
        return state

    if prompt_password or mode == "require":
        password = getpass("sudo password: ") if prompt_password else getpass("sudo password (required): ")
        if password and _sudo_validate_password(password):
            state.use_sudo = True
            state.requires_password = True
            state.password = password
            return state
        if mode == "require":
            print("ERROR: sudo access is required but credentials were rejected.", file=sys.stderr)
            raise SystemExit(1)

    return state


def _reset_privileges_for_tests():  # pragma: no cover - helper for unit tests
    state = _PRIV_STATE
    state.is_root = os.geteuid() == 0
    state.use_sudo = False
    state.requires_password = False
    state.password = None
    state.mode = "auto"
    state.configured = False


def run(
    cmd: Sequence[str],
    *,
    timeout: float = 10.0,
    optional: bool = False,
    needs_root: bool = False,
) -> CommandResult:
    """Execute ``cmd`` with guardrails, sudo awareness, and diagnostics."""

    global _WARNED_MISSING_SUDO
    start = time.perf_counter()
    display = " ".join(cmd)
    full_cmd = list(cmd)
    input_data: str | None = None

    if needs_root and not _PRIV_STATE.is_root:
        if not _PRIV_STATE.configured:
            configure_privileges()
        if _PRIV_STATE.use_sudo:
            if _PRIV_STATE.requires_password and _PRIV_STATE.password:
                full_cmd = ["sudo", "-S"] + full_cmd
                input_data = f"{_PRIV_STATE.password}\n"
            else:
                full_cmd = ["sudo", "-n"] + full_cmd
        else:
            if not optional and not _WARNED_MISSING_SUDO:
                print(
                    "INFO: Running without sudo; privileged command may fail: "
                    f"{display}",
                    file=sys.stderr,
                )
                _WARNED_MISSING_SUDO = True

    try:
        run_kwargs = dict(
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        if input_data is not None:
            completed = subprocess.run(full_cmd, input=input_data, **run_kwargs)
        else:
            completed = subprocess.run(full_cmd, stdin=subprocess.DEVNULL, **run_kwargs)
    except FileNotFoundError:
        duration = time.perf_counter() - start
        failed = full_cmd[0] if full_cmd else cmd[0]
        result = CommandResult(cmd=tuple(full_cmd), error=f"Command not found: {failed}", duration=duration)
        if not optional:
            print(f"WARNING: {result.error}", file=sys.stderr)
        _COMMAND_LOG.append(result)
        return result
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.output or "").strip()
        stderr = (exc.stderr or "").strip()
        duration = time.perf_counter() - start
        result = CommandResult(
            cmd=tuple(full_cmd),
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
            error=f"Timed out after {timeout:.1f}s: {' '.join(full_cmd)}",
            duration=duration,
        )
        print(f"WARNING: {result.error}", file=sys.stderr)
        _COMMAND_LOG.append(result)
        return result

    duration = time.perf_counter() - start
    stdout = completed.stdout.strip() if completed.stdout else ""
    stderr = completed.stderr.strip() if completed.stderr else ""
    result = CommandResult(
        cmd=tuple(full_cmd),
        stdout=stdout,
        stderr=stderr,
        returncode=completed.returncode,
        duration=duration,
    )

    if completed.returncode != 0:
        result.error = stderr or stdout or f"Exit code {completed.returncode}"
        level = "INFO" if optional else "WARNING"
        print(
            f"{level}: Command '{' '.join(full_cmd)}' exited with {completed.returncode}: {result.error}",
            file=sys.stderr,
        )

    _COMMAND_LOG.append(result)
    return result


def get_command_log() -> list[CommandResult]:
    """Return a snapshot of recorded command executions."""

    return list(_COMMAND_LOG)


def clear_command_log() -> None:
    """Reset recorded command executions (intended for tests)."""

    _COMMAND_LOG.clear()


def collect_system_info():
    info = {}
    for key, opt in [
        ("manufacturer", "-s system-manufacturer"),
        ("product_name", "-s system-product-name"),
        ("bios_version", "-s bios-version"),
    ]:
        result = run(["dmidecode"] + opt.split(), timeout=15.0, needs_root=True)
        if result.success and result.stdout:
            info[key] = result.stdout
    return info


def collect_cpu_info():
    raw = run(["lscpu"], timeout=10.0)
    data = {}
    for line in raw.stdout.splitlines():
        if ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        data[k] = v
    return data


def collect_memory_info():
    raw = run(["dmidecode", "-t", "memory"], timeout=20.0, needs_root=True)
    devices = []
    array_info = {}
    current_device = None
    section = None

    for line in raw.stdout.splitlines():
        line = line.rstrip()
        if not line or line.startswith("# dmidecode"):
            continue
        if line.startswith("Handle "):
            if current_device:
                devices.append(current_device)
                current_device = None
            continue
        if line.startswith("Physical Memory Array"):
            section = "array"
            continue
        if line.startswith("Memory Device"):
            section = "device"
            current_device = {}
            continue
        if ":" not in line:
            continue
        key, value = [x.strip() for x in line.split(":", 1)]
        if section == "array":
            array_info[key] = value
        elif section == "device" and current_device is not None:
            current_device[key] = value

    if current_device:
        devices.append(current_device)

    def parse_capacity(text):
        if not text:
            return None
        match = re.match(r"(\d+)\s*(\w+)", text)
        if not match:
            return None
        value = int(match.group(1))
        unit = match.group(2).upper()
        if unit.startswith("PB"):
            return value * 1024 * 1024
        if unit.startswith("TB"):
            return value * 1024
        if unit.startswith("GB"):
            return float(value)
        if unit.startswith("MB"):
            return float(value) / 1024
        return None

    max_capacity_gb = parse_capacity(array_info.get("Maximum Capacity"))
    try:
        declared_slots = int(array_info.get("Number Of Devices", "0").split()[0])
    except ValueError:
        declared_slots = None

    return {
        "devices": devices,
        "max_capacity_gb": max_capacity_gb,
        "ecc": array_info.get("Error Correction Type"),
        "slot_count": declared_slots,
    }


def collect_storage():
    raw = run(["lsblk", "-J", "-o", "NAME,MODEL,SIZE,TYPE,MOUNTPOINT,ROTA,TRAN"], timeout=15.0)
    if not raw.stdout:
        return []
    try:
        parsed = json.loads(raw.stdout)
    except json.JSONDecodeError:
        return []
    disks = []

    def recurse(entry):
        if entry.get("type") == "disk" and not entry.get("name", "").startswith("loop"):
            disks.append(entry)
        for child in entry.get("children", []):
            recurse(child)

    for block in parsed.get("blockdevices", []):
        recurse(block)
    return disks


def collect_nvme():
    if shutil.which("nvme") is None:
        return ""
    result = run(["nvme", "list"], timeout=15.0, optional=True)
    return result.stdout


def collect_gpu():
    pci = run(["lspci"], timeout=10.0)
    gpus_pci = [
        line for line in pci.stdout.splitlines()
        if any(tok in line.lower() for tok in ("vga", "3d", "display"))
    ]
    parsed_nv = []
    if shutil.which("nvidia-smi"):
        nvidia = run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], timeout=15.0, optional=True)
        for line in nvidia.stdout.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 2:
                parsed_nv.append({"name": parts[0], "memory": parts[1]})
    return gpus_pci, parsed_nv


def parse_size_to_gb(text):
    if not text or "No Module" in text:
        return 0.0
    match = re.search(r"(\d+)\s*(GB|MB)", text, re.IGNORECASE)
    if not match:
        return 0.0
    value = int(match.group(1))
    unit = match.group(2).upper()
    return value / 1024 if unit == "MB" else float(value)


def parse_speed_mts(text):
    if not text:
        return None
    matches = re.findall(r"(\d+)", text)
    if not matches:
        return None
    values = [int(value) for value in matches]
    for value in reversed(values):
        if value >= 1000:
            return value
    return max(values)


def metrics_from_data(cpu, mem_info, total_mem_mb, gpus_pci, gpus_nv, disks):
    threads = int(cpu.get("CPU(s)", "0").split()[0]) if cpu.get("CPU(s)") else 0
    sockets = int(cpu.get("Socket(s)", "1").split()[0]) if cpu.get("Socket(s)") else 1
    cores_per_socket = int(cpu.get("Core(s) per socket", "0").split()[0]) if cpu.get("Core(s) per socket") else 0
    cores = sockets * cores_per_socket if cores_per_socket else 0
    max_mhz = float(cpu.get("CPU max MHz", "0").split()[0]) if cpu.get("CPU max MHz") else 0.0
    cur_mhz = float(cpu.get("CPU MHz", "0").split()[0]) if cpu.get("CPU MHz") else 0.0
    min_mhz = float(cpu.get("CPU min MHz", "0").split()[0]) if cpu.get("CPU min MHz") else 0.0
    virtualization = cpu.get("Virtualization", "")

    mem_devices = mem_info.get("devices", [])
    mem_total_gb = total_mem_mb / 1024 if total_mem_mb else 0.0
    if mem_total_gb == 0.0:
        mem_total_gb = sum(parse_size_to_gb(dev.get("Size")) for dev in mem_devices)

    declared_slots = mem_info.get("slot_count")
    populated = len([d for d in mem_devices if parse_size_to_gb(d.get("Size")) > 0])
    if declared_slots:
        empty = max(declared_slots - populated, 0)
        slots = declared_slots
    else:
        slots = len([d for d in mem_devices if d.get("Locator")])
        empty = max(slots - populated, 0)

    speeds = [
        parse_speed_mts(d.get("Configured Memory Speed") or d.get("Speed"))
        for d in mem_devices
        if parse_speed_mts(d.get("Configured Memory Speed") or d.get("Speed"))
    ]
    configured_speed = max(speeds) if speeds else None

    has_dedicated_gpu = any(
        ("nvidia" in line.lower()) or ("amd" in line.lower() and "graphics" in line.lower())
        for line in gpus_pci
    )
    if not has_dedicated_gpu and gpus_nv:
        has_dedicated_gpu = True

    gpu_vram_gb = 0.0
    for gpu in gpus_nv:
        match_mib = re.search(r"(\d+)\s*MiB", gpu["memory"])
        match_gib = re.search(r"(\d+)\s*GiB", gpu["memory"])
        if match_gib:
            gpu_vram_gb = max(gpu_vram_gb, float(match_gib.group(1)))
        elif match_mib:
            gpu_vram_gb = max(gpu_vram_gb, int(match_mib.group(1)) / 1024)

    storage_nvme = sum(1 for d in disks if (d.get("tran") or "").lower() == "nvme")

    return {
        "cpu_model": cpu.get("Model name", "Unknown"),
        "cpu_arch": cpu.get("Architecture", ""),
        "threads": threads,
        "cores": cores,
        "cpu_max_ghz": max_mhz / 1000 if max_mhz else 0.0,
        "cpu_min_ghz": min_mhz / 1000 if min_mhz else 0.0,
        "cpu_cur_ghz": cur_mhz / 1000 if cur_mhz else 0.0,
        "virtualization": virtualization,
        "ram_total_gb": mem_total_gb,
        "ram_slots": slots,
        "ram_populated": populated,
        "ram_empty": empty,
        "ram_modules": mem_devices,
        "ram_max_capacity_gb": mem_info.get("max_capacity_gb"),
        "ram_ecc": mem_info.get("ecc"),
        "ram_configured_speed_mts": configured_speed,
        "has_dedicated_gpu": has_dedicated_gpu,
        "gpu_vram_gb": gpu_vram_gb,
        "storage_nvme": storage_nvme,
        "storage_total": len(disks),
    }


def role_rating(metrics):
    ratings = {}

    def pack(rating, summary, notes=None):
        return {"rating": rating, "summary": summary, "notes": notes or []}

    if metrics["threads"] >= 16 and metrics["ram_total_gb"] >= 32:
        ratings["Developer workstation"] = pack(
            "Excellent",
            "Plenty of CPU threads and RAM for IDEs, containers, and VMs."
        )
    elif metrics["threads"] >= 8 and metrics["ram_total_gb"] >= 16:
        ratings["Developer workstation"] = pack(
            "Good",
            "Solid balance; consider RAM or NVMe upgrades if workloads grow."
        )
    else:
        ratings["Developer workstation"] = pack(
            "Limited",
            "Basic dev work only; more cores or RAM would help."
        )

    server_notes = []
    if metrics["virtualization"]:
        server_notes.append(f"Virtualization extensions detected ({metrics['virtualization']}).")
    if metrics["ram_total_gb"] >= 64 and metrics["threads"] >= 24:
        ratings["Developer server"] = pack(
            "Good",
            "Comfortable for multiple VMs or container stacks.",
            server_notes
        )
    elif metrics["ram_total_gb"] >= 32 and metrics["threads"] >= 16:
        server_notes.append("Consider more RAM or ECC platform for heavier multi-tenant loads.")
        ratings["Developer server"] = pack(
            "Limited",
            "Can host a few services; heavier use may need upgrades.",
            server_notes
        )
    else:
        server_notes.append("Specs under typical server thresholds; keep workloads light.")
        ratings["Developer server"] = pack(
            "Not ideal",
            "Upgrade RAM/CPU or offload heavier services.",
            server_notes
        )

    ml_notes = []
    if metrics["has_dedicated_gpu"]:
        if metrics["gpu_vram_gb"] >= 16:
            ratings["LLM / ML"] = pack(
                "Fair",
                f"Discrete GPU with about {metrics['gpu_vram_gb']:.1f} GB VRAM supports small/medium models.",
                ml_notes
            )
        elif metrics["gpu_vram_gb"] >= 8:
            ml_notes.append("VRAM limits you to compact or quantized models.")
            ratings["LLM / ML"] = pack(
                "Limited",
                f"Approximately {metrics['gpu_vram_gb']:.1f} GB VRAM; use distilled models or consider external GPU.",
                ml_notes
            )
        else:
            ml_notes.append("GPU VRAM is minimal for ML; expect CPU-bound inference.")
            ratings["LLM / ML"] = pack(
                "Limited",
                "Add a higher-VRAM GPU or use cloud resources for serious ML.",
                ml_notes
            )
    else:
        ml_notes.append("No discrete GPU detected; ML workloads will be CPU-bound and slow.")
        ratings["LLM / ML"] = pack(
            "Not ideal",
            "Add a discrete GPU or use cloud resources.",
            ml_notes
        )

    media_notes = []
    if metrics["has_dedicated_gpu"]:
        ratings["Media / streaming"] = pack(
            "Good",
            "Discrete GPU should accelerate encoding and multiple streams.",
            media_notes
        )
    else:
        media_notes.append("Integrated graphics can handle light streaming; heavy multi-stream loads may struggle.")
        ratings["Media / streaming"] = pack(
            "Limited",
            "Consider adding a discrete GPU or hardware encoder.",
            media_notes
        )

    nas_notes = []
    if metrics["storage_total"] >= 3 or metrics["storage_nvme"] >= 2:
        nas_notes.append("Multiple drives present; add redundancy (RAID/ZFS) as needed.")
        ratings["NAS / DB"] = pack(
            "Fair",
            "Usable for lightweight NAS/DB duties.",
            nas_notes
        )
    else:
        nas_notes.append("Only one storage device detected; add more drives for redundancy and performance.")
        ratings["NAS / DB"] = pack(
            "Limited",
            "Expand storage and consider ECC memory for reliability.",
            nas_notes
        )

    return ratings


def storage_slot_hint(product_name, disks):
    if not product_name:
        return "Model name unavailable; consult the service manual for storage slot details."

    matched_hint = None
    for key, hint in STORAGE_HINTS.items():
        if product_name.startswith(key):
            matched_hint = hint
            break

    if not matched_hint:
        return "No model-specific storage slot data; inspect the chassis or vendor documentation."

    nvme_slots = matched_hint.get("nvme_slots")
    notes = matched_hint.get("notes", "")
    if nvme_slots is None:
        return notes or "Storage slot hint unavailable."

    nvme_present = sum(1 for d in disks if (d.get("tran") or "").lower() == "nvme")
    free_slots = nvme_slots - nvme_present
    if free_slots > 0:
        detail = f"Detected {nvme_present}/{nvme_slots} NVMe slots populated; about {free_slots} slot(s) likely free."
    else:
        detail = f"Detected {nvme_present}/{nvme_slots} NVMe slots populated."
    return f"{notes} {detail}".strip()


def upgrade_suggestions(metrics, disks, nvme_raw, storage_hint_text):
    tips = []

    if metrics["ram_empty"] > 0:
        tips.append(f"Populate the {metrics['ram_empty']} empty memory slot(s) to expand RAM.")
    elif metrics["ram_total_gb"] and metrics["ram_max_capacity_gb"]:
        if metrics["ram_total_gb"] < metrics["ram_max_capacity_gb"]:
            tips.append(f"Replace existing SODIMMs to move toward the {metrics['ram_max_capacity_gb']:.0f} GB platform ceiling.")
        else:
            tips.append("System is already at the reported maximum memory capacity.")

    if metrics["storage_total"] <= 1:
        tips.append("Only one storage device detected; add another NVMe/SATA drive for capacity or redundancy.")

    if not metrics["has_dedicated_gpu"]:
        tips.append("No discrete GPU detected; add one if ML or media workloads are important and the chassis supports it.")

    if storage_hint_text and "likely free" in storage_hint_text.lower():
        tips.append("Use the free M.2 slot for a second NVMe SSD if additional fast storage is needed.")

    if nvme_raw and "Device" not in nvme_raw:
        tips.append("Install nvme-cli for deeper NVMe diagnostics (temperature, firmware, spare space).")

    return tips


def format_markdown(system, cpu, metrics, mem_info, disks, gpus_pci, gpus_nv, ratings, tips, nvme_raw, storage_hint_text):
    host = socket.gethostname()
    manufacturer = system.get("manufacturer", "Unknown")
    product = system.get("product_name", "Unknown")
    bios = system.get("bios_version", "Unknown")

    freq_parts = []
    if metrics["cpu_min_ghz"]:
        freq_parts.append(f"min {metrics['cpu_min_ghz']:.2f} GHz")
    if metrics["cpu_cur_ghz"]:
        freq_parts.append(f"current {metrics['cpu_cur_ghz']:.2f} GHz")
    if metrics["cpu_max_ghz"]:
        freq_parts.append(f"max {metrics['cpu_max_ghz']:.2f} GHz")
    freq_line = ", ".join(freq_parts) if freq_parts else "Unavailable"

    ram_speed = f"{metrics['ram_configured_speed_mts']} MT/s" if metrics["ram_configured_speed_mts"] else "Unknown"
    max_capacity = f"{metrics['ram_max_capacity_gb']:.0f} GB" if metrics["ram_max_capacity_gb"] else "Unknown"
    ecc = metrics["ram_ecc"] or "Unknown / none"

    lines = []
    lines.append(f"# Hardware Assessment – {host}")
    lines.append("")
    lines.append("## System Summary")
    lines.append("| Item | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Model | {product} ({manufacturer}) |")
    lines.append(f"| BIOS | {bios} |")
    lines.append(f"| CPU | {metrics['cpu_model']} |")
    lines.append(f"| CPU Frequency | {freq_line} |")
    lines.append(f"| Cores / Threads | {metrics['cores']} / {metrics['threads']} |")
    lines.append(f"| RAM Installed | approximately {metrics['ram_total_gb']:.1f} GB across {metrics['ram_populated']} module(s) |")
    lines.append(f"| RAM Maximum (reported) | {max_capacity} |")
    lines.append(f"| RAM Configured Speed | {ram_speed} |")
    lines.append(f"| RAM ECC | {ecc} |")
    lines.append(f"| Virtualization | {metrics['virtualization'] or 'Unknown'} |")
    lines.append(f"| Storage Devices Detected | {metrics['storage_total']} (NVMe: {metrics['storage_nvme']}) |")
    lines.append("")

    lines.append("## Memory Modules")
    modules = metrics["ram_modules"]
    if modules:
        lines.append("| Slot | Size | Configured Speed | Part Number | Voltage |")
        lines.append("| --- | --- | --- | --- | --- |")
        for dev in modules:
            size = dev.get("Size", "Unknown")
            if size == "No Module Installed":
                continue
            slot = dev.get("Locator", "Unknown")
            speed = dev.get("Configured Memory Speed") or dev.get("Speed") or "Unknown"
            part = (dev.get("Part Number") or "Unknown").strip()
            voltage = dev.get("Configured Voltage") or dev.get("Maximum Voltage") or "Unknown"
            lines.append(f"| {slot} | {size} | {speed} | {part} | {voltage} |")
    else:
        lines.append("No module data available (dmidecode output was empty).")
    lines.append("")

    lines.append("## Storage Devices")
    if disks:
        lines.append("| Device | Model | Size | Type | Bus | Mountpoints |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for disk in disks:
            model = disk.get("model") or "Unknown"
            size = disk.get("size") or "Unknown"
            tran = (disk.get("tran") or "?").upper()
            drive_type = "SSD" if not disk.get("rota") else "HDD"
            mounts = sorted({child.get("mountpoint") for child in disk.get("children", []) if child.get("mountpoint")})
            mount_str = ", ".join(mounts) if mounts else "-"
            lines.append(f"| {disk['name']} | {model} | {size} | {drive_type} | {tran} | {mount_str} |")
    else:
        lines.append("No disks detected (lsblk returned nothing useful).")
    lines.append("")
    lines.append(f"**Storage Slot Insight:** {storage_hint_text}")
    lines.append("")

    lines.append("## GPU")
    if gpus_pci:
        lines.append("Detected PCI/PCIe display adapters:")
        for line in gpus_pci:
            lines.append(f"- {line}")
    else:
        lines.append("- No GPU entries found via lspci.")
    if gpus_nv:
        lines.append("")
        lines.append("| NVIDIA GPU | Reported VRAM |")
        lines.append("| --- | --- |")
        for gpu in gpus_nv:
            lines.append(f"| {gpu['name']} | {gpu['memory']} |")
    lines.append("")

    lines.append("## Role Suitability")
    lines.append("| Role | Rating | Notes |")
    lines.append("| --- | --- | --- |")
    for role, data in ratings.items():
        details = [data["summary"]] + data.get("notes", [])
        lines.append(f"| {role} | {data['rating']} | {'<br>'.join(details)} |")
    lines.append("")

    lines.append("## Upgrade Opportunities")
    if tips:
        for tip in tips:
            lines.append(f"- {tip}")
    else:
        lines.append("- No obvious upgrades suggested by current readings.")
    lines.append("")

    if nvme_raw:
        lines.append("## Raw `nvme list` Output")
        lines.append("```")
        lines.append(nvme_raw)
        lines.append("```")
        lines.append("")

    lines.append("## Command Notes")
    lines.append("- Run with sudo so dmidecode can read SMBIOS tables.")
    lines.append("- Install optional tools (nvme-cli, nvidia-smi) for fuller reports.")
    lines.append("- For macOS hosts, use system_profiler/ioreg equivalents instead; this script targets Linux.")
    lines.append("")

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None):
    parser = argparse.ArgumentParser(description="Hardware capability assessor")
    parser.add_argument(
        "--sudo-mode",
        choices=["auto", "skip", "require"],
        default="auto",
        help="How to handle privileged commands (default: auto)",
    )
    parser.add_argument(
        "--prompt-sudo",
        action="store_true",
        help="Prompt for sudo password if passwordless sudo is unavailable",
    )
    args = parser.parse_args(argv)

    try:
        configure_privileges(mode=args.sudo_mode, prompt_password=args.prompt_sudo)
    except SystemExit as exc:
        return exc.code

    if not _PRIV_STATE.is_root and not _PRIV_STATE.use_sudo:
        print(
            "WARNING: running without sudo; memory details may be incomplete (dmidecode needs root).",
            file=sys.stderr,
        )

    required_tools = ["dmidecode", "lscpu", "lsblk", "lspci", "free"]
    missing = [tool for tool in required_tools if shutil.which(tool) is None]
    if missing:
        print(f"Missing required tools: {', '.join(missing)}", file=sys.stderr)
        print("Install them before rerunning.", file=sys.stderr)
        return 1

    system = collect_system_info()
    cpu = collect_cpu_info()
    mem_info = collect_memory_info()
    total_mem_mb = None
    free_output = run(["free", "-m"], timeout=5.0)
    match = re.search(r"Mem:\s+(\d+)", free_output.stdout)
    if match:
        total_mem_mb = int(match.group(1))
    disks = collect_storage()
    nvme_raw = collect_nvme()
    gpus_pci, gpus_nv = collect_gpu()

    metrics = metrics_from_data(cpu, mem_info, total_mem_mb, gpus_pci, gpus_nv, disks)
    ratings = role_rating(metrics)
    storage_hint_text = storage_slot_hint(system.get("product_name"), disks)
    tips = upgrade_suggestions(metrics, disks, nvme_raw, storage_hint_text)
    report = format_markdown(system, cpu, metrics, mem_info, disks, gpus_pci, gpus_nv, ratings, tips, nvme_raw, storage_hint_text)

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
