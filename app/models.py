from sqlalchemy import Column, Integer, String
from app.database import Base


class Student(Base):
    """SQLAlchemy model representing the students table in SQLite."""

    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    course = Column(String, nullable=True)
    address = Column(String, nullable=True)
    enrollment_date = Column(String, nullable=True)

    def to_dict(self):
        """Convert student record to dictionary representation."""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "date_of_birth": self.date_of_birth,
            "email": self.email,
            "phone": self.phone,
            "course": self.course,
            "address": self.address,
            "enrollment_date": self.enrollment_date,
        }

    def __repr__(self):
        return f"<Student(id={self.student_id}, name='{self.name}', course='{self.course}')>"
