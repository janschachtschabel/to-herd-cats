"""Integration adapters: translate domain objects into external calls.

Pure adapters — no DB, no HTTP routing. Services and the runtime orchestrate
them; the adapters just talk to LiteLLM, MCP servers, Langfuse, etc.
"""
