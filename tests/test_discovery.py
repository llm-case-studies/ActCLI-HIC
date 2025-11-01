import subprocess

import pytest

from app import discovery


@pytest.fixture(autouse=True)
def reset_discovery(monkeypatch):
    # Ensure helpers we monkeypatch are restored automatically.
    yield


def _host(**kwargs):
    return discovery.DiscoveredHost(**kwargs)


def test_discover_hosts_groups_multiple_sources(monkeypatch):
    avahi_entries = [
        _host(hostname="example.local", address="192.168.1.10", source="avahi", tags=["avahi"], alias=None),
        _host(hostname="example.local", address="fe80::1", source="avahi", tags=["avahi"], alias=None),
    ]
    ssh_entries = [
        _host(
            hostname="example.local",
            address="example.local",
            source="ssh-config",
            tags=["ssh-config", "user:dev"],
            alias="dev@example.local",
        )
    ]

    monkeypatch.setattr(discovery, "discover_avahi", lambda: avahi_entries)
    monkeypatch.setattr(discovery, "discover_ssh_config", lambda: ssh_entries)

    results = discovery.discover_hosts()
    assert len(results) == 1
    entry = results[0]
    assert entry.hostname == "example.local"
    assert set(entry.addresses) == {"192.168.1.10", "fe80::1", "example.local"}
    assert set(entry.sources) == {"avahi", "ssh-config"}
    assert entry.warnings == []
    assert entry.ssh_aliases == ["dev@example.local"]


def test_discover_hosts_warns_without_ssh_config(monkeypatch):
    avahi_entries = [
        _host(hostname="solo.local", address="192.168.1.11", source="avahi", tags=["avahi"], alias=None)
    ]
    monkeypatch.setattr(discovery, "discover_avahi", lambda: avahi_entries)
    monkeypatch.setattr(discovery, "discover_ssh_config", lambda: [])

    results = discovery.discover_hosts()
    assert len(results) == 1
    entry = results[0]
    assert entry.hostname == "solo.local"
    assert entry.sources == ["avahi"]
    assert entry.warnings == ["No SSH configuration entry found; verify SSH access."]


def test_verify_ssh_success(monkeypatch):
    monkeypatch.setattr(discovery.shutil, "which", lambda tool: "/usr/bin/ssh" if tool == "ssh" else None)

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(discovery.subprocess, "run", fake_run)

    result = discovery.verify_ssh("example.local")
    assert result.reachable is True
    assert result.authenticated is True
    assert result.returncode == 0


def test_verify_ssh_permission_denied(monkeypatch):
    monkeypatch.setattr(discovery.shutil, "which", lambda tool: "/usr/bin/ssh" if tool == "ssh" else None)

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 255, stdout="", stderr="Permission denied (publickey)")

    monkeypatch.setattr(discovery.subprocess, "run", fake_run)

    result = discovery.verify_ssh("example.local")
    assert result.reachable is True
    assert result.authenticated is False
    assert result.returncode == 255


def test_verify_ssh_timeout(monkeypatch):
    monkeypatch.setattr(discovery.shutil, "which", lambda tool: "/usr/bin/ssh" if tool == "ssh" else None)

    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 6), output="", stderr="")

    monkeypatch.setattr(discovery.subprocess, "run", fake_run)

    result = discovery.verify_ssh("example.local")
    assert result.reachable is False
    assert result.authenticated is False
    assert result.returncode == -1


def test_avahi_decimal_sequences_are_decoded():
    avahi_encoded = "Acer-HL\\032\\09154\\058ab\\0583a\\058b1\\058ee\\0584a\\093"
    decoded = discovery._decode_avahi_name(avahi_encoded)
    assert decoded == "Acer-HL [54:ab:3a:b1:ee:4a]"
    assert discovery._sanitize_hostname(decoded) == "Acer-HL"


def test_parse_ssh_config_block_skips_wildcard():
    entries = list(discovery._parse_ssh_config_block(["ionos-*", "ionos-2c4g"], {}))
    aliases = [entry.alias for entry in entries]
    assert "ionos-*" not in aliases
    assert any(alias == "ionos-2c4g" for alias in aliases)
