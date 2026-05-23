"""create conversation tables

Revision ID: 001
Create Date: 2025-02-19
"""
"""from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('meta_data', JSON)
    )

    # Create chats table
    op.create_table(
        'chats',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('conversation_id', sa.String(), sa.ForeignKey('conversations.id')),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('meta_data', JSON)
    )

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('chat_id', sa.String(), sa.ForeignKey('chats.id')),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('meta_data', JSON)
    )

def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('chats')
    op.drop_table('conversations')"""


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