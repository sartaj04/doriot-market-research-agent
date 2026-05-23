"""add binary feedback to chat_messages

Revision ID: add_binary_feedback
Revises: 001
Create Date: 2025-02-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_binary_feedback'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add boolean feedback column to chat_messages
    op.add_column('chat_messages', sa.Column('feedback', sa.Boolean(), nullable=True))

def downgrade() -> None:
    op.drop_column('chat_messages', 'feedback')