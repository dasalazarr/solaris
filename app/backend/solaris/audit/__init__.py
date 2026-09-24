"""Audit log de solo anexar con cadena de hash (M4-T2, F08). Ver migrations/003_audit.sql."""

from solaris.audit.redact import redact_payload, scrub_text, summarize_text
from solaris.audit.store import (
    EVENT_TYPES,
    GENESIS,
    Actor,
    AuditError,
    AuditUnavailable,
    ChainReport,
    compute_hash,
    connect_reader,
    connect_writer,
    export_csv,
    iter_export_csv,
    query_events,
    record,
    record_safe,
    verify_chain,
    writer_configured,
)

__all__ = [
    "EVENT_TYPES",
    "GENESIS",
    "Actor",
    "AuditError",
    "AuditUnavailable",
    "ChainReport",
    "compute_hash",
    "connect_reader",
    "connect_writer",
    "export_csv",
    "iter_export_csv",
    "query_events",
    "record",
    "record_safe",
    "redact_payload",
    "scrub_text",
    "summarize_text",
    "verify_chain",
    "writer_configured",
]
