def upgrade() -> None:
    """Upgrade schema."""
    # 1. BẮT BUỘC xóa bảng con (kanjis) trước vì nó đang trỏ khóa ngoại tới bảng cha
    op.drop_index('ix_kanjis_id', table_name='kanjis')
    op.drop_table('kanjis')
    
    # 2. Sau đó mới được phép xóa bảng cha (kanji_sets)
    op.drop_index('ix_kanji_sets_id', table_name='kanji_sets')
    op.drop_table('kanji_sets')
    
    # 3. Thêm cột mới
    op.add_column('sets', sa.Column('type', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sets', 'type')
    
    # 1. Khi tạo lại thì BẮT BUỘC tạo bảng cha trước
    op.create_table('kanji_sets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('folder_path', sa.String(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_kanji_sets_id', 'kanji_sets', ['id'], unique=False)

    # 2. Sau đó mới tạo bảng con và gắn khóa ngoại
    op.create_table('kanjis',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('kanji', sa.String(length=255), nullable=False),
    sa.Column('hanviet', sa.String(length=255), nullable=False),
    sa.Column('hiragana', sa.String(length=255), nullable=False),
    sa.Column('meaning', sa.String(length=500), nullable=False),
    sa.Column('kanji_set_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['kanji_set_id'], ['kanji_sets.id'], name='kanjis_ibfk_1', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_kanjis_id', 'kanjis', ['id'], unique=False)