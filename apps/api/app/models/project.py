from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="Untitled Project")
    source_type = Column(String(50), nullable=False, default="youtube")  # youtube, upload, audio
    source_url = Column(String(1024), nullable=True)
    status = Column(String(50), nullable=False, default="DRAFT", index=True)  # DRAFT, PROCESSING, READY, etc.
    learning_level = Column(String(50), nullable=False, default="INTERMEDIATE")  # BEGINNER, INTERMEDIATE, ADVANCED, EXAM
    output_mode = Column(String(50), nullable=False, default="STANDARD")  # QUICK, STANDARD, DETAILED, EXAM
    visual_style = Column(String(50), nullable=False, default="HANDWRITTEN")  # HANDWRITTEN, ACADEMIC, INFOGRAPHIC
    page_count = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="projects")
    source = relationship("Source", back_populates="project", uselist=False, cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="project", uselist=False, cascade="all, delete-orphan")
    concepts = relationship("Concept", back_populates="project", cascade="all, delete-orphan", order_by="Concept.importance.desc()")
    pages = relationship("Page", back_populates="project", cascade="all, delete-orphan", order_by="Page.page_number")
    jobs = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="project", cascade="all, delete-orphan")
