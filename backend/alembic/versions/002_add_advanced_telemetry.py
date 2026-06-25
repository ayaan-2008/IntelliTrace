"""Add advanced telemetry columns - biochemical, environmental, physiological, biomechanical.

Revision ID: 002_advanced_telemetry
Revises: 001_initial
Create Date: 2025-06-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_advanced_telemetry"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Biochemical / Sweat Analysis
    op.add_column("telemetry", sa.Column("cortisol_level", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("lactate_level", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("skin_conductance", sa.Float(), nullable=True))

    # Advanced Physiological
    op.add_column("telemetry", sa.Column("ecg_value", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("respiration_rate", sa.Integer(), nullable=True))
    op.add_column("telemetry", sa.Column("hrv_rmssd", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("blood_pressure_systolic", sa.Integer(), nullable=True))
    op.add_column("telemetry", sa.Column("blood_pressure_diastolic", sa.Integer(), nullable=True))

    # Environmental
    op.add_column("telemetry", sa.Column("uv_index", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("pm25", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("voc_level", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("barometric_pressure", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("ambient_light", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("humidity", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("ambient_temperature", sa.Float(), nullable=True))

    # Biomechanical
    op.add_column("telemetry", sa.Column("body_orientation", sa.String(20), nullable=True))
    op.add_column("telemetry", sa.Column("gait_symmetry", sa.Float(), nullable=True))
    op.add_column("telemetry", sa.Column("fall_detected", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("telemetry", "fall_detected")
    op.drop_column("telemetry", "gait_symmetry")
    op.drop_column("telemetry", "body_orientation")
    op.drop_column("telemetry", "ambient_temperature")
    op.drop_column("telemetry", "humidity")
    op.drop_column("telemetry", "ambient_light")
    op.drop_column("telemetry", "barometric_pressure")
    op.drop_column("telemetry", "voc_level")
    op.drop_column("telemetry", "pm25")
    op.drop_column("telemetry", "uv_index")
    op.drop_column("telemetry", "blood_pressure_diastolic")
    op.drop_column("telemetry", "blood_pressure_systolic")
    op.drop_column("telemetry", "hrv_rmssd")
    op.drop_column("telemetry", "respiration_rate")
    op.drop_column("telemetry", "ecg_value")
    op.drop_column("telemetry", "skin_conductance")
    op.drop_column("telemetry", "lactate_level")
    op.drop_column("telemetry", "cortisol_level")
