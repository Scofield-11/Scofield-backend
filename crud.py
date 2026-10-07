from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import models
import schemas


def get_all_vocabularies(db: Session):
    return db.query(models.Vocabulary).all()


def get_vocabulary(db: Session, vocab_id: int):
    return db.query(models.Vocabulary).filter(models.Vocabulary.id == vocab_id).first()


def create_vocabulary(db: Session, vocab: schemas.VocabularyCreate):
    db_vocab = models.Vocabulary(
        word=vocab.word.strip(),
        hanviet=(vocab.hanviet or "").strip(),
        hiragana=(vocab.hiragana or "").strip(),
        meaning=vocab.meaning.strip(),
        language=vocab.language or "ja"
    )
    db.add(db_vocab)
    db.commit()
    db.refresh(db_vocab)
    return db_vocab


def update_vocabulary(db: Session, vocab_id: int, vocab: schemas.VocabularyUpdate):
    db_vocab = get_vocabulary(db, vocab_id)
    if not db_vocab:
        return None
    db_vocab.word = vocab.word.strip()
    db_vocab.hanviet = (vocab.hanviet or "").strip()
    db_vocab.hiragana = (vocab.hiragana or "").strip()
    db_vocab.meaning = vocab.meaning.strip()
    if vocab.language:
        db_vocab.language = vocab.language.strip()
    db.commit()
    db.refresh(db_vocab)
    return db_vocab


def delete_vocabulary(db: Session, vocab_id: int):
    db_vocab = get_vocabulary(db, vocab_id)
    if not db_vocab:
        return None
    db.delete(db_vocab)
    db.commit()
    return db_vocab


def bulk_import_vocabularies(db: Session, raw_text: str):
    """
    Nhận vào chuỗi văn bản nhiều dòng, mỗi dòng có dạng:
    Từ vựng | Ý nghĩa
    Tự động tách bằng dấu '|', bỏ dòng trống hoặc dòng sai định dạng,
    rồi lưu tất cả vào database trong 1 lần commit.
    """
    lines = raw_text.strip().split("\n")
    created_items = []
    skipped_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "|" not in line:
            skipped_lines.append(line)
            continue

        parts = line.split("|", 1)
        word = parts[0].strip()
        meaning = parts[1].strip()

        if not word or not meaning:
            skipped_lines.append(line)
            continue

        db_vocab = models.Vocabulary(word=word, meaning=meaning, hanviet="", hiragana="", language="ja")
        db.add(db_vocab)
        created_items.append(db_vocab)

    db.commit()

    for item in created_items:
        db.refresh(item)

    return {
        "created_count": len(created_items),
        "skipped_count": len(skipped_lines),
        "skipped_lines": skipped_lines,
        "items": created_items,
    }


def get_random_vocabularies(db: Session, limit: int = 10):
    return db.query(models.Vocabulary).order_by(func.rand()).limit(limit).all()

def create_set_with_vocabularies(db: Session, title: str, raw_text: str, folder_path: str = "", language: str = "ja", set_type: str = "vocab"):
    new_set = models.Set(title=title, folder_path=folder_path, language=language or "ja", type=set_type)
    db.add(new_set)
    db.flush() 

    # BỔ SUNG: Cho phép tạo học phần rỗng để "giữ chỗ" cho folder
    if not raw_text or not raw_text.strip():
        db.commit()
        return 0, []

    lines = raw_text.strip().split('\n')
    imported_count = 0
    errors = []
    
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue
        # Bỏ qua các dòng phân đoạn tiêu đề (ví dụ: **Từ 1 - 30** hoặc ---)
        if line_clean.startswith('---') or line_clean.startswith('**'):
            continue

        if '|' in line_clean:
            parts = [p.strip() for p in line_clean.split('|')]

            if len(parts) >= 4:
                # Định dạng 4 cột: Chữ Hán | Hán Việt | Cách đọc | Ý nghĩa
                raw_kanji = parts[0]
                raw_hanviet = parts[1]
                raw_hiragana = parts[2]
                meaning = parts[3]

                if not raw_kanji and raw_hiragana:
                    # Từ thuần Hiragana/Katakana khuyết Kanji
                    word = raw_hiragana
                    hiragana = ""
                    hanviet = raw_hanviet
                else:
                    word = raw_kanji
                    hanviet = raw_hanviet
                    hiragana = raw_hiragana

            elif len(parts) == 3:
                # Định dạng 3 cột: Từ vựng | Cách đọc | Ý nghĩa
                word = parts[0] if parts[0] else parts[1]
                hiragana = parts[1] if parts[0] else ""
                hanviet = ""
                meaning = parts[2]

            elif len(parts) == 2:
                # Định dạng 2 cột: Từ vựng | Ý nghĩa
                word = parts[0]
                hanviet = ""
                hiragana = ""
                meaning = parts[1]

            else:
                word = ""
                meaning = ""

            if word and meaning:
                new_vocab = models.Vocabulary(
                    word=word,
                    hanviet=hanviet,
                    hiragana=hiragana,
                    meaning=meaning,
                    language=language or "ja",
                    set_id=new_set.id
                )
                db.add(new_vocab)
                imported_count += 1
            else:
                errors.append(f"Dòng {idx + 1}: Bị trống từ vựng hoặc ý nghĩa.")
        else:
            errors.append(f"Dòng {idx + 1}: Thiếu ký tự phân cách '|'.")
            
    if imported_count == 0:
        db.rollback()
        return None, errors
        
    db.commit()
    return imported_count, errors

# Cập nhật các hàm lấy dữ liệu
def get_all_sets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(
        models.Set.id,
        models.Set.title,
        models.Set.folder_path,
        models.Set.language,
        models.Set.type,
        models.Set.created_at,
        func.count(models.Vocabulary.id).label("vocab_count")
    ).outerjoin(models.Vocabulary, models.Set.id == models.Vocabulary.set_id)\
     .group_by(models.Set.id).offset(skip).limit(limit).all()

def get_set_detail(db: Session, set_id: int):
    return db.query(models.Set).options(joinedload(models.Set.vocabularies)).filter(models.Set.id == set_id).first()

def get_all_vocabularies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Vocabulary).offset(skip).limit(limit).all()