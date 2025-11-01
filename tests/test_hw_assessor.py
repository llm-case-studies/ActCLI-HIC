import types

import agents.hw_assessor as assessor


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
