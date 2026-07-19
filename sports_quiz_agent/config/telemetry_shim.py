"""
Telemetry import shim for ChromaDB on locked-down Windows machines.

ChromaDB unconditionally imports OpenTelemetry's gRPC-based OTLP span
exporter at package-import time (``chromadb/telemetry/opentelemetry/__init__.py``),
regardless of whether telemetry is actually enabled. That import pulls in
``grpcio``'s compiled ``cygrpc`` native extension.

On machines governed by Windows Defender Application Control, Smart App
Control, or similar corporate endpoint-security policies, loading an
unsigned/untrusted native DLL like ``cygrpc.pyd`` can be blocked outright,
which crashes the whole app before a single line of our own code runs --
even though we never use ChromaDB's telemetry feature.

This module pre-registers a lightweight, no-op stand-in for the specific
gRPC exporter submodule in ``sys.modules`` *before* ChromaDB is imported,
so ChromaDB's ``from ... import OTLPSpanExporter`` is satisfied without
ever executing grpc's native code. If ``grpc`` imports fine on the current
machine, this shim does nothing and gets out of the way.

Must be called before the first ``import chromadb`` anywhere in the app.
"""

from __future__ import annotations

import os
import sys
import types


def patch_chromadb_grpc_telemetry() -> None:
    """Idempotently neutralize ChromaDB's hard dependency on grpc's native extension."""

    # Belt-and-braces: also tell ChromaDB not to bother sending telemetry at all.
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

    module_name = "opentelemetry.exporter.otlp.proto.grpc.trace_exporter"

    if module_name in sys.modules:
        return  # Already imported (real or previously patched) -- nothing to do.

    try:
        import grpc  # noqa: F401

        return  # grpc's native extension loads fine here; no patch needed.
    except ImportError:
        pass  # Fall through and install the no-op stand-in below.

    stub = types.ModuleType(module_name)

    class OTLPSpanExporter:  # noqa: N801 - name must match the real upstream class
        """No-op stand-in used only when grpc's native extension can't load."""

        def __init__(self, *args, **kwargs) -> None:
            pass

        def export(self, *args, **kwargs):
            return None

        def shutdown(self, *args, **kwargs) -> None:
            return None

    stub.OTLPSpanExporter = OTLPSpanExporter
    sys.modules[module_name] = stub
