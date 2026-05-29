from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from db.database import get_db
from db.models import User, Project, File
from auth.firebase import verify_token
import uuid

router = APIRouter()


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    class Config: from_attributes = True

class FileCreate(BaseModel):
    name: str
    content: str = ""
    language: str = "python"

class FileUpdate(BaseModel):
    content: str

class FileResponse(BaseModel):
    id: str
    name: str
    content: str
    language: str
    class Config: from_attributes = True


# ─── User routes ──────────────────────────────────────────────────────────────

@router.post("/auth/login")
def login(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Called after Google Sign-In. Creates user in DB if first time,
    or updates their info if returning user.
    """
    user = db.query(User).filter(User.id == current_user["uid"]).first()

    if not user:
        user = User(
            id=current_user["uid"],
            email=current_user["email"],
            name=current_user["name"],
            photo=current_user["photo"],
        )
        db.add(user)

        # Create a default project for new users
        default_project = Project(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="My First Project",
        )
        db.add(default_project)

        # Add a starter file
        starter_file = File(
            id=str(uuid.uuid4()),
            project_id=default_project.id,
            name="main.py",
            content="# Welcome to AgentCoder!\nprint('Hello, World!')\n",
            language="python",
        )
        db.add(starter_file)
        db.commit()
    else:
        user.name = current_user["name"]
        user.photo = current_user["photo"]
        db.commit()

    return {
        "uid": user.id,
        "email": user.email,
        "name": user.name,
        "photo": user.photo,
    }


@router.get("/auth/me")
def get_me(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user["uid"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"uid": user.id, "email": user.email, "name": user.name, "photo": user.photo}


# ─── Project routes ───────────────────────────────────────────────────────────

@router.get("/projects", response_model=List[ProjectResponse])
def get_projects(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    return db.query(Project).filter(Project.user_id == current_user["uid"]).all()


@router.post("/projects", response_model=ProjectResponse)
def create_project(
    body: ProjectCreate,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    project = Project(
        id=str(uuid.uuid4()),
        user_id=current_user["uid"],
        name=body.name,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user["uid"]
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"deleted": project_id}


# ─── File routes ──────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/files", response_model=List[FileResponse])
def get_files(
    project_id: str,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user["uid"]
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.files


@router.post("/projects/{project_id}/files", response_model=FileResponse)
def create_file(
    project_id: str,
    body: FileCreate,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user["uid"]
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    file = File(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=body.name,
        content=body.content,
        language=body.language,
    )
    db.add(file)
    db.commit()
    db.refresh(file)
    return file


@router.put("/projects/{project_id}/files/{file_id}", response_model=FileResponse)
def update_file(
    project_id: str,
    file_id: str,
    body: FileUpdate,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    file = db.query(File).join(Project).filter(
        File.id == file_id,
        Project.id == project_id,
        Project.user_id == current_user["uid"]
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    file.content = body.content
    db.commit()
    db.refresh(file)
    return file


@router.delete("/projects/{project_id}/files/{file_id}")
def delete_file(
    project_id: str,
    file_id: str,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    file = db.query(File).join(Project).filter(
        File.id == file_id,
        Project.id == project_id,
        Project.user_id == current_user["uid"]
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    db.delete(file)
    db.commit()
    return {"deleted": file_id}