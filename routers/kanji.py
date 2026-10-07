from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import models
import schemas
from database import get_db

router = APIRouter(
    tags=["kanji"]
)

class KanjiUpdate(BaseModel):
    kanji: str
    hanviet: Optional[str] = ""
    hiragana: Optional[str] = ""
    meaning: str

@router.get("/kanji-sets")
def get_kanji_sets(db: Session = Depends(get_db)):
    sets = db.query(models.Set).filter(models.Set.type == "kanji").all()
    result = []
    for s in sets:
        vocab_count = db.query(models.Vocabulary).filter(models.Vocabulary.set_id == s.id).count()
        result.append({
            "id": s.id,
            "title": s.title,
            "folder_path": s.folder_path,
            "created_at": s.created_at,
            "vocab_count": vocab_count,
            "kanjis": []
        })
    return result

@router.get("/kanji-sets/{set_id}")
def get_kanji_set_detail(set_id: int, db: Session = Depends(get_db)):
    db_set = db.query(models.Set).filter(models.Set.id == set_id, models.Set.type == "kanji").first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Không tìm thấy học phần Kanji")
    
    kanjis = db.query(models.Vocabulary).filter(models.Vocabulary.set_id == set_id).all()
    kanji_list = []
    for k in kanjis:
        kanji_list.append({
            "id": k.id,
            "kanji": k.word,
            "hanviet": k.hanviet,
            "hiragana": k.hiragana,
            "meaning": k.meaning,
            "kanji_set_id": k.set_id
        })
    
    return {
        "id": db_set.id,
        "title": db_set.title,
        "folder_path": db_set.folder_path,
        "created_at": db_set.created_at,
        "kanjis": kanji_list
    }

@router.delete("/kanji-sets/{set_id}")
def delete_kanji_set(set_id: int, db: Session = Depends(get_db)):
    db_set = db.query(models.Set).filter(models.Set.id == set_id, models.Set.type == "kanji").first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Không tìm thấy học phần Kanji")
    db.delete(db_set)
    db.commit()
    return {"message": "Đã xóa học phần Kanji thành công"}

@router.delete("/kanji/{kanji_id}")
def delete_kanji(kanji_id: int, db: Session = Depends(get_db)):
    db_vocab = db.query(models.Vocabulary).filter(models.Vocabulary.id == kanji_id).first()
    if not db_vocab:
        raise HTTPException(status_code=404, detail="Không tìm thấy Kanji")
    db.delete(db_vocab)
    db.commit()
    return {"message": "Đã xóa Kanji"}

@router.put("/kanji/{kanji_id}")
def update_kanji(kanji_id: int, payload: KanjiUpdate, db: Session = Depends(get_db)):
    db_vocab = db.query(models.Vocabulary).filter(models.Vocabulary.id == kanji_id).first()
    if not db_vocab:
        raise HTTPException(status_code=404, detail="Không tìm thấy Kanji")
    
    db_vocab.word = payload.kanji.strip()
    db_vocab.hanviet = payload.hanviet.strip() if payload.hanviet else ""
    db_vocab.hiragana = payload.hiragana.strip() if payload.hiragana else ""
    db_vocab.meaning = payload.meaning.strip()
    
    db.commit()
    db.refresh(db_vocab)
    
    return {
        "id": db_vocab.id,
        "kanji": db_vocab.word,
        "hanviet": db_vocab.hanviet,
        "hiragana": db_vocab.hiragana,
        "meaning": db_vocab.meaning,
        "kanji_set_id": db_vocab.set_id
    }

