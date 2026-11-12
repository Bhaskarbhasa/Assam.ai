"""
Unit Tests for Conversation Flow, Follow-ups, and Hallucination Control.
"""
from app.core_agent import HardwareQAAgent
from app.memory_context import ConversationSession

def test_ram_upgrade_query():
    session = ConversationSession("test_flow")
    agent = HardwareQAAgent(session)

    res = agent.process_query("Can I add more RAM, and how much?")
    assert "get_dmi_memory" in res["tool_called"]
    assert "16 GB" in res["answer"]
    assert "64 GB" in res["answer"]
    assert "1 empty slot" in res["answer"]

def test_nvme_storage_query():
    session = ConversationSession("test_flow")
    agent = HardwareQAAgent(session)

    res = agent.process_query("Is my SSD NVMe?")
    assert "get_block_devices" in res["tool_called"]
    assert "Yes" in res["answer"]
    assert "NVMe SSD" in res["answer"]

def test_follow_up_caching():
    session = ConversationSession("test_flow")
    agent = HardwareQAAgent(session)

    # First turn: ask about RAM
    res1 = agent.process_query("Can I add more RAM?")
    assert res1["category"] == "memory"
    assert "get_dmi_memory" in res1["tool_called"]

    # Second turn: follow-up on free slots (should use cached memory data)
    res2 = agent.process_query("How many free slots do I have?")
    assert "cached" in res2["tool_called"]
    assert "1 free" in res2["answer"]

    # Third turn: switch topic to GPU
    res3 = agent.process_query("And what about the GPU?")
    assert res3["category"] == "gpu"
    assert "get_pci_devices" in res3["tool_called"]
    assert "AMD" in res3["answer"]

def test_anti_hallucination_on_missing_data():
    session = ConversationSession("test_flow")
    agent = HardwareQAAgent(session)

    res = agent.process_query("Who manufactured my laptop casing plastic?")
    assert "I cannot determine this hardware detail from system data" in res["answer"]
