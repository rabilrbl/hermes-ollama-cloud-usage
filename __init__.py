"""Ollama Cloud usage plugin for Hermes Agent."""

from . import schemas
from . import tools


def register(ctx):
    ctx.register_tool(
        name="check_ollama_cloud_usage",
        toolset="ollama_cloud",
        schema=schemas.CHECK_OLLAMA_CLOUD_USAGE,
        handler=lambda args, **kw: tools.check_ollama_cloud_usage(args, **kw),
    )
