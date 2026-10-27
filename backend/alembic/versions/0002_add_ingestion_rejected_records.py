"""Add rejected_records to ingestion_jobs

Revision ID: 0002_add_ingestion_rejected_records
Revises: 0001_initial_schema
Create Date: 2026-10-27 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_ingestion_rejected_records"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ingestion_jobs", sa.Column("rejected_records", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("ingestion_jobs", "rejected_records")
