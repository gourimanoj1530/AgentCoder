from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)          # Firebase UID
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    photo = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    projects = relationship("Project", back_populates="user", cascade="all, delete")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="projects")
    files = relationship("File", back_populates="project", cascade="all, delete")


class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, default="")
    language = Column(String, default="python")

    project = relationship("Project", back_populates="files")