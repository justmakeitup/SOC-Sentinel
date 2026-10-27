"""Initial schema migration for Sentinel SOC Platform

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-27 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("is_mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_created_at", "users", ["created_at"])

    # 2. log_sources table
    op.create_table(
        "log_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default=sa.text("90")),
        sa.Column("config_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_log_sources_id", "log_sources", ["id"])
    op.create_index("ix_log_sources_name", "log_sources", ["name"], unique=True)
    op.create_index("ix_log_sources_source_type", "log_sources", ["source_type"])
    op.create_index("ix_log_sources_status", "log_sources", ["status"])
    op.create_index("ix_log_sources_hostname", "log_sources", ["hostname"])
    op.create_index("ix_log_sources_created_at", "log_sources", ["created_at"])

    # 3. ingestion_jobs table
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("log_source_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("batch_identifier", sa.String(length=128), nullable=True),
        sa.Column("events_processed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("events_failed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("bytes_ingested", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["log_source_id"], ["log_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_jobs_id", "ingestion_jobs", ["id"])
    op.create_index("ix_ingestion_jobs_log_source_id", "ingestion_jobs", ["log_source_id"])
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])
    op.create_index("ix_ingestion_jobs_batch_id", "ingestion_jobs", ["batch_identifier"])
    op.create_index("ix_ingestion_jobs_started_at", "ingestion_jobs", ["started_at"])

    # 4. normalized_security_events table
    op.create_table(
        "normalized_security_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("log_source_id", sa.Uuid(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_action", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("source_ip", sa.String(length=45), nullable=True),
        sa.Column("source_port", sa.Integer(), nullable=True),
        sa.Column("destination_ip", sa.String(length=45), nullable=True),
        sa.Column("destination_port", sa.Integer(), nullable=True),
        sa.Column("protocol", sa.String(length=16), nullable=True),
        sa.Column("user_name", sa.String(length=128), nullable=True),
        sa.Column("host_name", sa.String(length=255), nullable=True),
        sa.Column("process_name", sa.String(length=255), nullable=True),
        sa.Column("process_path", sa.String(length=512), nullable=True),
        sa.Column("command_line", sa.Text(), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("extra_fields", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["log_source_id"], ["log_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_hash", name="uq_event_hash_deduplication"),
    )
    op.create_index("ix_events_id", "normalized_security_events", ["id"])
    op.create_index("ix_events_source_id", "normalized_security_events", ["log_source_id"])
    op.create_index("ix_events_timestamp", "normalized_security_events", ["timestamp"])
    op.create_index("ix_events_ingested_at", "normalized_security_events", ["ingested_at"])
    op.create_index("ix_events_event_type", "normalized_security_events", ["event_type"])
    op.create_index("ix_events_event_action", "normalized_security_events", ["event_action"])
    op.create_index("ix_events_severity", "normalized_security_events", ["severity"])
    op.create_index("ix_events_src_ip", "normalized_security_events", ["source_ip"])
    op.create_index("ix_events_dst_ip", "normalized_security_events", ["destination_ip"])
    op.create_index("ix_events_user_name", "normalized_security_events", ["user_name"])
    op.create_index("ix_events_host_name", "normalized_security_events", ["host_name"])
    op.create_index("idx_events_source_time", "normalized_security_events", ["log_source_id", "timestamp"])
    op.create_index("idx_events_type_time", "normalized_security_events", ["event_type", "timestamp"])
    op.create_index("idx_events_src_ip_time", "normalized_security_events", ["source_ip", "timestamp"])
    op.create_index("idx_events_dst_ip_time", "normalized_security_events", ["destination_ip", "timestamp"])

    # 5. detection_rules table
    op.create_table(
        "detection_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("time_window_seconds", sa.Integer(), nullable=False, server_default=sa.text("300")),
        sa.Column("threshold_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("mitre_tactic", sa.String(length=64), nullable=True),
        sa.Column("mitre_technique", sa.String(length=64), nullable=True),
        sa.Column("rule_logic", sa.JSON(), nullable=False),
        sa.Column("remediation_guidance", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rules_id", "detection_rules", ["id"])
    op.create_index("ix_rules_code", "detection_rules", ["rule_code"], unique=True)
    op.create_index("ix_rules_name", "detection_rules", ["name"])
    op.create_index("ix_rules_severity", "detection_rules", ["severity"])
    op.create_index("ix_rules_is_active", "detection_rules", ["is_active"])
    op.create_index("ix_rules_mitre_tactic", "detection_rules", ["mitre_tactic"])
    op.create_index("ix_rules_mitre_technique", "detection_rules", ["mitre_technique"])
    op.create_index("ix_rules_created_at", "detection_rules", ["created_at"])

    # 6. incidents table
    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_number", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("lead_analyst_id", sa.Uuid(), nullable=True),
        sa.Column("containment_details", sa.Text(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lead_analyst_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_id", "incidents", ["id"])
    op.create_index("ix_incidents_number", "incidents", ["incident_number"], unique=True)
    op.create_index("ix_incidents_title", "incidents", ["title"])
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"])
    op.create_index("idx_incidents_status_sev", "incidents", ["status", "severity"])

    # 7. security_alerts table
    op.create_table(
        "security_alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("deduplication_key", sa.String(length=128), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("context_data", sa.JSON(), nullable=False),
        sa.Column("assigned_to_id", sa.Uuid(), nullable=True),
        sa.Column("incident_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["detection_rules.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_id", "security_alerts", ["id"])
    op.create_index("ix_alerts_rule_id", "security_alerts", ["rule_id"])
    op.create_index("ix_alerts_title", "security_alerts", ["title"])
    op.create_index("ix_alerts_severity", "security_alerts", ["severity"])
    op.create_index("ix_alerts_status", "security_alerts", ["status"])
    op.create_index("ix_alerts_dedup_key", "security_alerts", ["deduplication_key"])
    op.create_index("ix_alerts_assigned_to", "security_alerts", ["assigned_to_id"])
    op.create_index("ix_alerts_incident_id", "security_alerts", ["incident_id"])
    op.create_index("ix_alerts_created_at", "security_alerts", ["created_at"])
    op.create_index("idx_alerts_status_sev", "security_alerts", ["status", "severity"])
    op.create_index("idx_alerts_dedup_time", "security_alerts", ["deduplication_key", "created_at"])

    # 8. investigation_notes table
    op.create_table(
        "investigation_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("note_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notes_id", "investigation_notes", ["id"])
    op.create_index("ix_notes_incident_id", "investigation_notes", ["incident_id"])
    op.create_index("ix_notes_author_id", "investigation_notes", ["author_id"])
    op.create_index("ix_notes_created_at", "investigation_notes", ["created_at"])

    # 9. audit_events table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("client_ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_id", "audit_events", ["id"])
    op.create_index("ix_audit_actor_id", "audit_events", ["actor_id"])
    op.create_index("ix_audit_action", "audit_events", ["action"])
    op.create_index("ix_audit_resource_type", "audit_events", ["resource_type"])
    op.create_index("ix_audit_resource_id", "audit_events", ["resource_id"])
    op.create_index("ix_audit_created_at", "audit_events", ["created_at"])
    op.create_index("idx_audit_resource", "audit_events", ["resource_type", "resource_id"])
    op.create_index("idx_audit_action_time", "audit_events", ["action", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("investigation_notes")
    op.drop_table("security_alerts")
    op.drop_table("incidents")
    op.drop_table("detection_rules")
    op.drop_table("normalized_security_events")
    op.drop_table("ingestion_jobs")
    op.drop_table("log_sources")
    op.drop_table("users")
