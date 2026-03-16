from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from typing import List

from database import get_db, engine, Base
from models import Note

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


@app.get("/api/notes", response_model=List[NoteResponse])
async def get_notes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).order_by(Note.created_at.desc()))
    return result.scalars().all()


@app.post("/api/notes", response_model=NoteResponse, status_code=201)
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_db)):
    db_note = Note(title=note.title, content=note.content)
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note


@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)
    await db.commit()
    return {"ok": True}
