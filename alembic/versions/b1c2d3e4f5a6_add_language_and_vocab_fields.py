"""add language and vocab fields for N3 support

Revision ID: b1c2d3e4f5a6
Revises: abcdef123456
Create Date: 2026-09-28 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'abcdef123456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Thêm cột language vào bảng sets
    op.add_column('sets', sa.Column('language', sa.String(length=20), server_default='ja', nullable=True))

    # 2. Thêm 3 cột hanviet, hiragana, language vào bảng vocabularies
    op.add_column('vocabularies', sa.Column('hanviet', sa.String(length=255), nullable=True))
    op.add_column('vocabularies', sa.Column('hiragana', sa.String(length=255), nullable=True))
    op.add_column('vocabularies', sa.Column('language', sa.String(length=20), server_default='ja', nullable=True))

    # 3. Cập nhật dữ liệu cũ để đảm bảo tương thích
    op.execute("UPDATE sets SET language = 'ja' WHERE language IS NULL")
    op.execute("UPDATE vocabularies SET language = 'ja' WHERE language IS NULL")
    op.execute("UPDATE vocabularies SET hanviet = '' WHERE hanviet IS NULL")
    op.execute("UPDATE vocabularies SET hiragana = '' WHERE hiragana IS NULL")


def downgrade() -> None:
    op.drop_column('vocabularies', 'language')
    op.drop_column('vocabularies', 'hiragana')
    op.drop_column('vocabularies', 'hanviet')
    op.drop_column('sets', 'language')
