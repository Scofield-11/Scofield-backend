"""Merge_Kanji_To_Vocab_And_Optimize

Revision ID: afadea808e85
Revises: b1c2d3e4f5a6
Create Date: 2026-10-06 13:15:41.735333

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'afadea808e85'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Bỏ qua lỗi nếu bảng hoặc khoá không tồn tại bằng Raw SQL "IF EXISTS"
    
    # 1. Xoá bảng con kanjis (Tự động xoá index kèm theo)
    op.execute("DROP TABLE IF EXISTS kanjis;")
    
    # 2. Xoá bảng cha kanji_sets
    op.execute("DROP TABLE IF EXISTS kanji_sets;")
    
    # 3. Thêm cột mới. Sử dụng cơ chế kiểm tra thủ công để tránh lỗi nếu cột đã lỡ được tạo
    conn = op.get_bind()
    result = conn.execute(sa.text("SHOW COLUMNS FROM sets LIKE 'type'")).fetchone()
    if not result:
        op.add_column('sets', sa.Column('type', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    result = conn.execute(sa.text("SHOW COLUMNS FROM sets LIKE 'type'")).fetchone()
    if result:
        op.drop_column('sets', 'type')
    
    # 1. Khi tạo lại thì BẮT BUỘC tạo bảng cha trước
    op.create_table('kanji_sets',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('title', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('folder_path', mysql.VARCHAR(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_kanji_sets_id', 'kanji_sets', ['id'], unique=False)

    # 2. Sau đó mới tạo bảng con và gắn khóa ngoại
    op.create_table('kanjis',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('kanji', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('hanviet', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('hiragana', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('meaning', mysql.VARCHAR(length=500), nullable=False),
    sa.Column('kanji_set_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['kanji_set_id'], ['kanji_sets.id'], name='kanjis_ibfk_1', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_kanjis_id', 'kanjis', ['id'], unique=False)