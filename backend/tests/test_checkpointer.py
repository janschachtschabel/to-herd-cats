"""Tests for the persistent LangGraph checkpointer (M5.4).

A graph that interrupts is run with a SQLite saver; a brand-new saver on the
same file (a simulated restart) resumes it, proving the paused state survives.
The graph module's checkpointer swap is covered too.
"""

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.runtime.checkpointer import open_sqlite_checkpointer
from app.runtime.graph import get_checkpointer, set_checkpointer


class _S(TypedDict, total=False):
    decision: dict
    done: bool


def _pause_graph(saver):
    def node(state):
        decision = interrupt({"ask": "approve?"})
        return {"decision": decision, "done": True}

    builder = StateGraph(_S)
    builder.add_node("n", node)
    builder.add_edge(START, "n")
    builder.add_edge("n", END)
    return builder.compile(checkpointer=saver)


async def test_sqlite_checkpointer_survives_restart(tmp_path):
    path = str(tmp_path / "ckpt.db")
    config = {"configurable": {"thread_id": "t1"}}

    saver1, conn1 = await open_sqlite_checkpointer(path)
    out1 = await _pause_graph(saver1).ainvoke({}, config=config)
    assert "__interrupt__" in out1  # paused, state written to the file
    await conn1.close()

    # Simulated restart: a brand-new saver/connection on the same file.
    saver2, conn2 = await open_sqlite_checkpointer(path)
    out2 = await _pause_graph(saver2).ainvoke(Command(resume={"action": "accept"}), config=config)
    await conn2.close()

    assert out2["done"] is True
    assert out2["decision"] == {"action": "accept"}


def test_set_checkpointer_swaps_and_restores():
    original = get_checkpointer()
    try:
        sentinel = MemorySaver()
        set_checkpointer(sentinel)
        assert get_checkpointer() is sentinel
    finally:
        set_checkpointer(original)
    assert get_checkpointer() is original
