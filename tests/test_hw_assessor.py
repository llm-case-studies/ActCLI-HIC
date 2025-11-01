import subprocess

import pytest

import agents.hw_assessor as assessor


@pytest.fixture(autouse=True)
def reset_state():
    assessor.clear_command_log()
    assessor._reset_privileges_for_tests()
    assessor._WARNED_MISSING_SUDO = False
    yield
    assessor.clear_command_log()
    assessor._reset_privileges_for_tests()
    assessor._WARNED_MISSING_SUDO = False


def test_parse_size_to_gb_handles_gb():
    assert assessor.parse_size_to_gb("32 GB") == 32.0


def test_parse_size_to_gb_handles_mb():
    assert assessor.parse_size_to_gb("512 MB") == 0.5


def test_parse_speed_mts_parses_digits():
    assert assessor.parse_speed_mts("DDR5-4800") == 4800


def test_storage_slot_hint_matches_known_model():
    disks = [
        {"tran": "nvme"},
        {"tran": "sata"},
    ]
    message = assessor.storage_slot_hint("Raider GE78 HX 14VGG", disks)
    assert "NVMe slots" in message
    assert "2" in message


def test_role_rating_produces_categories():
    cpu = {"CPU(s)": "16", "Socket(s)": "1", "Core(s) per socket": "8"}
    mem_info = {"devices": [], "slot_count": 2, "max_capacity_gb": 64, "ecc": "None"}
    metrics = assessor.metrics_from_data(
        cpu,
        mem_info,
        total_mem_mb=65536,
        gpus_pci=["Mock VGA"],
        gpus_nv=[],
        disks=[{"tran": "nvme"}],
    )
    ratings = assessor.role_rating(metrics)
    assert set(ratings) == {
        "Developer workstation",
        "Developer server",
        "LLM / ML",
        "Media / streaming",
        "NAS / DB",
    }


def test_upgrade_suggestions_reacts_to_empty_slots():
    metrics = {
        "ram_empty": 1,
        "ram_total_gb": 16,
        "ram_max_capacity_gb": 64,
        "storage_total": 1,
        "has_dedicated_gpu": False,
    }
    tips = assessor.upgrade_suggestions(metrics, disks=[], nvme_raw="", storage_hint_text="")
    assert any("memory slot" in tip.lower() for tip in tips)


def test_run_success_captures_stdout(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        assert kwargs.get("capture_output")
        assert kwargs.get("text")
        assert kwargs.get("stdin") is subprocess.DEVNULL
        assert kwargs.get("timeout") == pytest.approx(1.0)
        return subprocess.CompletedProcess(cmd, 0, stdout="hello\n", stderr="")

    monkeypatch.setattr(assessor.subprocess, "run", fake_run)

    result = assessor.run(["echo", "hello"], timeout=1.0)
    assert result.success
    assert result.stdout == "hello"
    assert result.stderr == ""
    assert result.returncode == 0
    assert not result.timed_out
    assert assessor.get_command_log()[:1] == [result]


def test_run_timeout_marks_failure(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout"), output="partial", stderr="err")

    monkeypatch.setattr(assessor.subprocess, "run", fake_run)

    result = assessor.run(["sleep", "3"], timeout=0.5)
    assert not result.success
    assert result.timed_out
    assert "Timed out" in (result.error or "")
    assert result.stdout == "partial"
    assert result.stderr == "err"


def test_run_non_zero_exit_reports_error(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="boom")

    monkeypatch.setattr(assessor.subprocess, "run", fake_run)

    result = assessor.run(["false"], timeout=1.0)
    assert not result.success
    assert result.error
    assert result.returncode == 2


def test_run_needs_root_wraps_with_sudo(monkeypatch):
    state = assessor._PRIV_STATE
    state.is_root = False
    state.configured = True
    state.use_sudo = True
    state.requires_password = False

    captured = {}

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(assessor.subprocess, "run", fake_run)

    result = assessor.run(["dmidecode", "-s", "system-manufacturer"], needs_root=True)
    assert result.success
    assert captured["cmd"][:2] == ["sudo", "-n"]


def test_run_needs_root_prompts_with_password(monkeypatch):
    state = assessor._PRIV_STATE
    state.is_root = False
    state.configured = True
    state.use_sudo = True
    state.requires_password = True
    state.password = "secret"

    captured = {}

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        captured["input"] = kwargs.get("input")
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(assessor.subprocess, "run", fake_run)

    result = assessor.run(["dmidecode", "-t", "memory"], needs_root=True)
    assert result.success
    assert captured["cmd"][:2] == ["sudo", "-S"]
    assert captured["input"] == "secret\n"
