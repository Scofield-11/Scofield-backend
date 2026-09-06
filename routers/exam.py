from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/exams",
    tags=["exams"]
)

@router.post("/import")
def import_exam(payload: schemas.ExamImport, db: Session = Depends(get_db)):
    new_exam = models.Exam(title=payload.title)
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)

    lines = payload.raw_text.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) == 6:
            q = models.ExamQuestion(
                exam_id=new_exam.id,
                question=parts[0], 
                opt1=parts[1], 
                opt2=parts[2], 
                opt3=parts[3], 
                opt4=parts[4],
                correct_ans=int(parts[5])
            )
            db.add(q)
            
    db.commit()
    return {"message": "Tạo bài test thành công", "exam_id": new_exam.id}

@router.get("")
def get_exams(db: Session = Depends(get_db)):
    return db.query(models.Exam).all()

@router.get("/{exam_id}")
def get_exam_detail(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài thi")
    
    return {
        "id": exam.id,
        "title": exam.title,
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "options": [q.opt1, q.opt2, q.opt3, q.opt4],
                "correct_ans": q.correct_ans
            } for q in exam.questions
        ]
    }

@router.put("/{exam_id}")
def update_exam(exam_id: int, payload: schemas.ExamImport, db: Session = Depends(get_db)):
    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài thi")
    
    exam.title = payload.title
    db.query(models.ExamQuestion).filter(models.ExamQuestion.exam_id == exam_id).delete()
    
    lines = payload.raw_text.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) == 6:
            q = models.ExamQuestion(
                exam_id=exam.id,
                question=parts[0], 
                opt1=parts[1], 
                opt2=parts[2], 
                opt3=parts[3], 
                opt4=parts[4],
                correct_ans=int(parts[5])
            )
            db.add(q)
            
    db.commit()
    return {"message": "Cập nhật thành công"}

@router.delete("/{exam_id}")
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài thi")
    
    db.delete(exam)
    db.commit()
    return {"message": "Đã xóa bài thi"}

@router.post("/{exam_id}/history")
def save_exam_history(exam_id: int, payload: schemas.ExamHistoryCreate, db: Session = Depends(get_db)):
    history = models.ExamHistory(
        exam_id=exam_id,
        score=payload.score,
        total=payload.total,
        wrong_details=payload.wrong_details
    )
    db.add(history)
    db.commit()
    return {"message": "Đã lưu lịch sử làm bài"}

@router.get("/history/all")
def get_all_history(db: Session = Depends(get_db)):
    histories = db.query(models.ExamHistory).order_by(models.ExamHistory.created_at.desc()).all()
    result = []
    for h in histories:
        result.append({
            "id": h.id,
            "examId": h.exam_id,
            "title": h.exam.title if h.exam else "Bài thi đã xóa",
            "score": h.score,
            "total": h.total,
            "date": h.created_at.strftime("%H:%M - %d/%m/%Y"),
            "wrongDetails": h.wrong_details
        })
    return result