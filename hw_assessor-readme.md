  # Hardware Assessor Script

  Generates a Markdown report summarizing CPU, memory, storage, GPU details, role suitability, and upgrade ideas using standard Linux tools.

  ## 1. Prerequisites

  - **Python 3.7+**
  - **sudo access** (needed for dmidecode).
  - **Packages**
    ```bash
    sudo apt update
    sudo apt install dmidecode lshw nvme-cli pciutils i2c-tools

  - Optional: install the matching nvidia-utils-* package so nvidia-smi can report VRAM.

  Check availability:

  for cmd in dmidecode lscpu lsblk lspci free; do which "$cmd" >/dev/null || echo "missing $cmd"; done

  ## 2. Installation

  1. Place hw_assessor.py somewhere convenient (e.g. ~/Docs/).
  2. Mark it executable:

     chmod +x ~/Docs/hw_assessor.py

  ## 3. Usage

  Run with sudo to pull SMBIOS data:

  cd ~/Docs
  sudo ./hw_assessor.py | tee "hw_assessor-$(hostname).md"

  The script emits Markdown; redirect or pipe it to a file for sharing. Missing tools are reported on stderr but the script keeps running with whatever data is available.

  ## 4. Output Overview

  - System Summary — model, BIOS, CPU, frequency range, cores/threads, total RAM, configured speed, ECC status, virtualization, disk count.
  - Memory Modules — per-slot size, speed, part number, voltage plus platform maximum capacity.
  - Storage Devices — disk model/size/type, bus, and mountpoints; includes a model-specific storage slot hint when known.
  - GPU — lspci display adapters and nvidia-smi VRAM table (if available).
  - Role Suitability — ratings for developer workstation/server, LLM/ML, media work, NAS/DB.
  - Upgrade Opportunities — actionable reminders based on empty RAM slots, platform ceiling, storage layout, GPU presence.
  - Raw nvme list — included when nvme-cli is present.

  ## 5. Customization

  - Extend STORAGE_HINTS for other models (product_name prefix -> slot metadata).
  - Tweak thresholds in role_rating() and heuristics in upgrade_suggestions() to match your environment.
  - If you need plain text instead of Markdown, adapt format_markdown() or add another formatter.

  ## 6. Deploy to Other Machines

  Copy hw_assessor.py and this README to your other hosts (Dell-Inspiron, iMac Debian, Acer HL, OMV ELBO, HP Envy Ubuntu, Beelink). Install the prerequisites, then run with sudo:

  sudo ./hw_assessor.py | tee ~/Docs/hw_assessor-$(hostname).md

  ## 7. macOS Note

  The script is Linux-specific. On macOS, rely on:

  - system_profiler SPHardwareDataType
  - system_profiler SPMemoryDataType
  - diskutil list
    or rewrite the script to call macOS equivalents.

  ## 8. Troubleshooting

  - Permission denied / missing data: rerun with sudo.
  - Command not found: install the package listed in prerequisites.
  - No nvme output: install nvme-cli or ignore that section if the system only has SATA disks.
  - SPD hidden: some BIOS revisions hide SPD; update firmware if modules show “No Module Installed.”

  ## 9. Version Tracking

  Use git to track tweaks:

  cd ~/Docs
  git init
  git add hw_assessor.py hw_assessor-readme.md
  git commit -m "Add hardware assessor script (Markdown report)"


