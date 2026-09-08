from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
import models
import schemas
from database import get_db

router = APIRouter(
    tags=["kanji"]
)

@router.get("/kanji-sets", response_model=list[schemas.KanjiSetOut])
def get_kanji_sets(db: Session = Depends(get_db)):
    return db.query(models.KanjiSet).options(joinedload(models.KanjiSet.kanjis)).order_by(models.KanjiSet.id.desc()).all()

@router.post("/kanji-sets/bulk-import")
def import_kanji_sets(payload: schemas.KanjiBulkImportRequest, db: Session = Depends(get_db)):
    new_set = models.KanjiSet(title=payload.title.strip())
    db.add(new_set)
    db.flush()

    lines = payload.raw_text.strip().split('\n')
    imported_count = 0
    errors = []
    
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue
        parts = [p.strip() for p in line_clean.split('|')]
        if len(parts) >= 4:
            kanji = models.Kanji(
                kanji=parts[0],
                hanviet=parts[1],
                hiragana=parts[2],
                meaning=parts[3],
                kanji_set_id=new_set.id
            )
            db.add(kanji)
            imported_count += 1
        else:
            errors.append(f"Dòng {idx + 1}: Thiếu cột dữ liệu (Yêu cầu 4 cột).")
    
    if imported_count == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="Không tìm thấy từ vựng Kanji hợp lệ nào.")
        
    db.commit()
    return {"message": f"Đã tạo học phần với {imported_count} từ vựng Kanji.", "errors": errors}

@router.delete("/kanji-sets/{kanji_set_id}")
def delete_kanji_set(kanji_set_id: int, db: Session = Depends(get_db)):
    db_set = db.query(models.KanjiSet).filter(models.KanjiSet.id == kanji_set_id).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Không tìm thấy học phần Kanji")
    db.delete(db_set)
    db.commit()
    return {"message": "Đã xóa học phần Kanji thành công"}

@router.put("/kanji/{kanji_id}", response_model=schemas.KanjiOut)
def update_kanji(kanji_id: int, payload: schemas.KanjiUpdate, db: Session = Depends(get_db)):
    db_kanji = db.query(models.Kanji).filter(models.Kanji.id == kanji_id).first()
    if not db_kanji:
        raise HTTPException(status_code=404, detail="Không tìm thấy chữ Kanji")
    
    db_kanji.kanji = payload.kanji.strip()
    db_kanji.hanviet = payload.hanviet.strip()
    db_kanji.hiragana = payload.hiragana.strip()
    db_kanji.meaning = payload.meaning.strip()
    db.commit()
    db.refresh(db_kanji)
    return db_kanji

@router.delete("/kanji/{kanji_id}")
def delete_kanji(kanji_id: int, db: Session = Depends(get_db)):
    db_kanji = db.query(models.Kanji).filter(models.Kanji.id == kanji_id).first()
    if not db_kanji:
        raise HTTPException(status_code=404, detail="Không tìm thấy chữ Kanji")
    db.delete(db_kanji)
    db.commit()
    return {"message": "Đã xóa chữ Kanji"}