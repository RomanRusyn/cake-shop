"""Create cakes table

Revision ID: 6eb3ad4c319c
Revises: 
Create Date: 2026-09-07 17:47:11.148747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6eb3ad4c319c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cakes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("price_kopiyky", sa.Integer(), nullable=False),
        sa.Column("weight_grams", sa.Integer(), nullable=False),
        sa.CheckConstraint("price_kopiyky > 0"),
        sa.CheckConstraint("weight_grams > 0"),
    )


def downgrade() -> None:
    op.drop_table("cakes")
