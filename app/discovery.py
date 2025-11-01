"""Utilities for discovering potential hosts (Avahi, SSH config, etc.)."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

_AVAHI_ESCAPE = re.compile(r"\\(\d{3})")
_AVAHI_CTRL = re.compile(r"\\(?:00[0-9]|01[0-9]|02[0-9]|03[0-9]|040)")


@dataclass
class DiscoveredHost:
    hostname: str
    address: str | None
    source: str
    tags: list[str]
    alias: str | None = None


@dataclass
class AggregatedDiscovery:
    hostname: str
    addresses: list[str]
    sources: list[str]
    tags: list[str]
    ssh_aliases: list[str]
    warnings: list[str]


@dataclass
class SSHCheckResult:
    target: str
    reachable: bool
    authenticated: bool
    returncode: int
    stdout: str
    stderr: str


def _run_command(cmd: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess:
    """Run a command with guardrails; return completed process."""

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        stdin=subprocess.DEVNULL,
    )


def _decode_avahi_name(name: str) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(1)
        base = 8 if set(token) <= {"0", "1", "2", "3", "4", "5", "6", "7"} else 10
        try:
            value = int(token, base)
            if value < 32:
                return " "
            return chr(value)
        except ValueError:
            return " "

    return _AVAHI_ESCAPE.sub(repl, name)


def _sanitize_hostname(name: str) -> str:
    printable = "".join(ch for ch in name if ch.isprintable())
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.: ")
    cleaned = "".join(ch for ch in printable if ch in allowed)
    cleaned = cleaned.strip(" .")
    if " " in cleaned:
        cleaned = cleaned.split()[0]
    return cleaned


def normalize_hostname(name: str) -> str:
    cleaned = _sanitize_hostname(name).lower()
    if not cleaned:
        return ""
    token = cleaned.split()[0]
    if token.endswith(".local"):
        token = token[:-6]
    return token


def _preferred_hostname(entry: DiscoveredHost) -> str:
    target = entry.address if entry.source == "ssh-config" and entry.address else entry.hostname
    cleaned = _sanitize_hostname(target)
    return cleaned or entry.hostname


def discover_avahi(service_type: str = "_workstation._tcp", timeout: float = 5.0) -> list[DiscoveredHost]:
    """Discover hosts advertised through Avahi/mDNS."""

    if shutil.which("avahi-browse") is None:
        return []

    cmd = ["avahi-browse", "-ptr", service_type]
    try:
        proc = _run_command(cmd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return []

    hosts: list[DiscoveredHost] = []
    for line in proc.stdout.splitlines():
        parts = line.strip().split(";")
        if len(parts) < 8:
            continue
        record_type = parts[0]
        if not record_type or record_type[0] not in {"=", "+"}:
            continue
        raw_name = _decode_avahi_name(parts[3])
        cleaned_name = _AVAHI_CTRL.sub(" ", raw_name)
        hostname = _sanitize_hostname(cleaned_name)
        address = parts[7] or None
        tags: list[str] = ["avahi", service_type]
        clean_host = hostname.rstrip(".")
        hosts.append(DiscoveredHost(hostname=clean_host, address=address, source="avahi", tags=tags))
    return hosts


def _base_hostname(alias: str) -> str:
    if "@" in alias:
        return alias.split("@", 1)[1]
    return alias


def _parse_ssh_config_block(host_aliases: list[str], options: dict[str, str]) -> Iterator[DiscoveredHost]:
    target = options.get("hostname")
    user = options.get("user")
    port = options.get("port")

    for alias in host_aliases:
        if "*" in alias or "?" in alias:
            continue
        base = _base_hostname(alias)
        address = target or base or None
        tags = ["ssh-config"]
        if user and user not in alias:
            tags.append(f"user:{user}")
        if port:
            tags.append(f"port:{port}")
        yield DiscoveredHost(
            hostname=base or alias,
            address=address,
            source="ssh-config",
            tags=tags,
            alias=alias,
        )


def discover_ssh_config(paths: Iterable[Path] | None = None) -> list[DiscoveredHost]:
    """Parse SSH config files for host definitions."""

    if paths is None:
        paths = [Path.home() / ".ssh" / "config"]

    discovered: list[DiscoveredHost] = []

    for path in paths:
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        current_hosts: list[str] = []
        options: dict[str, str] = {}

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("host "):
                if current_hosts:
                    discovered.extend(_parse_ssh_config_block(current_hosts, options))
                parts = shlex.split(line)
                aliases = [alias for alias in parts[1:] if alias != "*"]
                current_hosts = aliases
                options = {}
                continue
            if not current_hosts:
                continue
            match = re.match(r"(\S+)\s+(.*)", line)
            if not match:
                continue
            key = match.group(1).lower()
            value = match.group(2).strip()
            options[key] = value

        if current_hosts:
            discovered.extend(_parse_ssh_config_block(current_hosts, options))

    return discovered


def discover_hosts() -> list[AggregatedDiscovery]:
    """Return a merged, de-duplicated list of discovered hosts."""

    aggregates: dict[str, dict[str, set[str] | str | list[str]]] = {}

    def ensure_group(entry: DiscoveredHost) -> dict[str, set[str] | str | list[str]]:
        key_candidate = entry.address if entry.source == "ssh-config" and entry.address else entry.hostname
        key = normalize_hostname(key_candidate) or normalize_hostname(entry.hostname) or entry.hostname.lower()
        group = aggregates.get(key)
        if group is None:
            group = {
                "hostname": _preferred_hostname(entry),
                "addresses": set(),
                "sources": set(),
                "tags": set(),
                "ssh_aliases": set(),
                "warnings": [],
            }
            aggregates[key] = group
        return group

    for entry in discover_avahi():
        group = ensure_group(entry)
        if entry.address:
            group["addresses"].add(entry.address)
        group["sources"].add(entry.source)
        group["tags"].update(entry.tags)
        preferred = _preferred_hostname(entry)
        if not group.get("hostname"):
            group["hostname"] = preferred

    for entry in discover_ssh_config():
        group = ensure_group(entry)
        if entry.address:
            group["addresses"].add(entry.address)
        group["sources"].add(entry.source)
        group["tags"].update(entry.tags)
        if entry.alias:
            group["ssh_aliases"].add(entry.alias)
        preferred = _preferred_hostname(entry)
        if preferred:
            group["hostname"] = preferred

    aggregated_list: list[AggregatedDiscovery] = []
    for key in sorted(aggregates.keys()):
        group = aggregates[key]
        sources = sorted(group["sources"])  # type: ignore[arg-type]
        warnings: list[str] = list(group["warnings"])  # type: ignore[list-item]
        if "ssh-config" not in sources:
            warnings.append("No SSH configuration entry found; verify SSH access.")
        display_name = _sanitize_hostname(group["hostname"]) if group.get("hostname") else ""
        display_name = display_name or group.get("hostname") or next(iter(group["addresses"]), "")  # type: ignore[arg-type]
        aggregated_list.append(
            AggregatedDiscovery(
                hostname=display_name,
                addresses=sorted(group["addresses"]),  # type: ignore[arg-type]
                sources=sources,
                tags=sorted(group["tags"]),  # type: ignore[arg-type]
                ssh_aliases=sorted(group["ssh_aliases"]),  # type: ignore[arg-type]
                warnings=warnings,
            )
        )

    return aggregated_list


def verify_ssh(target: str, timeout: float = 5.0) -> SSHCheckResult:
    if shutil.which("ssh") is None:
        return SSHCheckResult(
            target=target,
            reachable=False,
            authenticated=False,
            returncode=-1,
            stdout="",
            stderr="ssh executable not found",
        )

    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout={:.0f}".format(timeout),
        "-o",
        "NumberOfPasswordPrompts=0",
        "-o",
        "StrictHostKeyChecking=no",
        target,
        "exit",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 1,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        stderr = (exc.stderr or "") + "\ncommand timed out"
        return SSHCheckResult(
            target=target,
            reachable=False,
            authenticated=False,
            returncode=-1,
            stdout=(exc.output or ""),
            stderr=stderr.strip(),
        )

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    reachable = proc.returncode == 0 or "Permission denied" in stderr
    authenticated = proc.returncode == 0
    return SSHCheckResult(
        target=target,
        reachable=reachable,
        authenticated=authenticated,
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
    )
