# Sudo Configuration Guidance

Assessments call standard read-only tools (`dmidecode`, `lscpu`, `lsblk`, `lspci`, `free`, optional `nvme`). Many require elevated privileges on Linux. Below are deployment options that avoid prompting users mid-run.

## Option A – passwordless sudo for existing user
Grant the existing account (e.g., `alex`) passwordless access to only the binaries we invoke:

```bash
sudo visudo
```

Add a drop-in under `/etc/sudoers.d/hic-assessor`:

```
Cmnd_Alias HIC_CMDS = /usr/sbin/dmidecode, /usr/bin/lscpu, /usr/bin/lsblk, /usr/bin/lspci, /usr/bin/free, /usr/sbin/nvme
alex ALL=(ALL) NOPASSWD: HIC_CMDS
```

This limits the scope: the user still needs their password for unrelated commands, yet assessments can run unattended.  Repeat for every target user you rely on.

## Option B – dedicated service account
1. Create a new user purely for HIC (e.g., `hicsvc`).
2. Install the assessor (`pip install actcli-hw-assessor`) in that user’s environment.
3. Provide an SSH key from the controller machine.
4. Create a sudoers rule:
   ```
   Cmnd_Alias HIC_CMDS = /usr/sbin/dmidecode, /usr/bin/lscpu, /usr/bin/lsblk, /usr/bin/lspci, /usr/bin/free, /usr/sbin/nvme
   hicsvc ALL=(root) NOPASSWD: HIC_CMDS
   ```
5. Set the host’s `ssh_target` to `hicsvc@hostname`.

Advantages: easier to audit and revoke without touching interactive user accounts.

## Option C – run without sudo
If privileged commands are impossible, set `allow_privileged=false` for the host (`PATCH /api/hosts/{id}`).  Assessments will still gather basic data (CPU via `/proc`, memory totals via `free`, etc.) but DIMM slot details and certain storage hints will be missing.  The UI surfaces the reduced coverage.

## Capturing password interactively?
We intentionally avoid collecting sudo passwords.  Passing them from the SPA to the backend introduces significant security and storage concerns (transport, audit, rotation).  Instead we recommend one of the NOPASSWD approaches above.  If interactive prompts become necessary, plan on brokering them over a secure channel (e.g., WebSocket + short-lived secrets) and scrubbing all logs.

## Shipping the assessor binary
Currently we expect the target host to have `actcli-hw-assessor` installed.  Future tasks:
- Package a standalone zip/appimage that can be copied over SSH before execution.
- Check `python3 -m agents.hw_assessor` failure and fall back to uploading the module for ephemeral execution.
- Add health checks to warn when the assessor is missing or outdated.

Track these improvements in the backlog under “Immediate Next Steps”.
