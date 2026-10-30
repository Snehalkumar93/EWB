from datetime import date
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student
from app.schemas import (
    StudentCreate,
    StudentResponse,
    StudentUpdatePatch,
    StudentUpdatePut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new student record",
    description="Creates a new student record with auto-generated student_id and stores it in SQLite.",
)
@router.post(
    "/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_student(student_in: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student in the database."""
    try:
        db_student = Student(
            name=student_in.name,
            date_of_birth=str(student_in.date_of_birth),
            email=str(student_in.email) if student_in.email else None,
            phone=student_in.phone,
            course=student_in.course,
            address=student_in.address,
            enrollment_date=(
                str(student_in.enrollment_date) if student_in.enrollment_date else None
            ),
        )
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return db_student
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to create student: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while creating the student record.",
        )


@router.get(
    "",
    response_model=List[StudentResponse],
    status_code=status.HTTP_200_OK,
    summary="List all students with optional filters",
    description="Retrieve all students sorted by student_id ascending. Supports filtering by name, course, and date_of_birth.",
)
@router.get(
    "/",
    response_model=List[StudentResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_students(
    name: Optional[str] = Query(None, description="Case-insensitive partial search on student name"),
    course: Optional[str] = Query(None, description="Case-insensitive partial search on course"),
    date_of_birth: Optional[date] = Query(None, description="Exact date of birth (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Retrieve students with optional filtering by name, course, and date_of_birth."""
    try:
        query = db.query(Student)

        if name and name.strip():
            query = query.filter(Student.name.ilike(f"%{name.strip()}%"))

        if course and course.strip():
            query = query.filter(Student.course.ilike(f"%{course.strip()}%"))

        if date_of_birth:
            query = query.filter(Student.date_of_birth == str(date_of_birth))

        students = query.order_by(Student.student_id.asc()).all()
        return students
    except Exception as exc:
        logger.error(f"Failed to fetch students: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while fetching student records.",
        )


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a student by ID",
    description="Retrieve a single student record by their unique student_id.",
)
def get_student_by_id(
    student_id: int = Path(
        ...,
        gt=0,
        description="The unique positive ID of the student",
        examples=[1],
    ),
    db: Session = Depends(get_db),
):
    """Retrieve a student record by student_id."""
    try:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found.",
            )
        return student
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to fetch student with ID {student_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while fetching the student record.",
        )


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Replace all details of a student",
    description="Full update of an existing student record. Replaces all editable fields.",
)
def update_student_put(
    student_id: int = Path(
        ...,
        gt=0,
        description="The unique positive ID of the student",
        examples=[1],
    ),
    student_in: StudentUpdatePut = ...,
    db: Session = Depends(get_db),
):
    """Full update of student record (replaces all editable fields)."""
    try:
        db_student = db.query(Student).filter(Student.student_id == student_id).first()
        if not db_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found.",
            )

        # Replace all editable fields
        db_student.name = student_in.name
        db_student.date_of_birth = str(student_in.date_of_birth)
        db_student.email = str(student_in.email) if student_in.email else None
        db_student.phone = student_in.phone
        db_student.course = student_in.course
        db_student.address = student_in.address
        db_student.enrollment_date = (
            str(student_in.enrollment_date) if student_in.enrollment_date else None
        )

        db.commit()
        db.refresh(db_student)
        return db_student
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to update student with ID {student_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while updating the student record.",
        )


@router.patch(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a student",
    description="Partial update of an existing student record. Only supplied fields are updated.",
)
def update_student_patch(
    student_id: int = Path(
        ...,
        gt=0,
        description="The unique positive ID of the student",
        examples=[1],
    ),
    patch_in: StudentUpdatePatch = ...,
    db: Session = Depends(get_db),
):
    """Partial update of student record (preserves omitted fields)."""
    try:
        update_data = patch_in.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="At least one field must be provided for partial update.",
            )

        db_student = db.query(Student).filter(Student.student_id == student_id).first()
        if not db_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found.",
            )

        # Update only explicitly supplied fields
        for field, value in update_data.items():
            if field in ("date_of_birth", "enrollment_date"):
                setattr(db_student, field, str(value) if value is not None else None)
            elif field == "email":
                setattr(db_student, field, str(value) if value is not None else None)
            else:
                setattr(db_student, field, value)

        db.commit()
        db.refresh(db_student)
        return db_student
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to patch student with ID {student_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while partially updating the student record.",
        )


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a student record",
    description="Deletes a student record by student_id from the database. Returns HTTP 204 with no content.",
)
def delete_student(
    student_id: int = Path(
        ...,
        gt=0,
        description="The unique positive ID of the student",
        examples=[1],
    ),
    db: Session = Depends(get_db),
):
    """Delete a student record by student_id."""
    try:
        db_student = db.query(Student).filter(Student.student_id == student_id).first()
        if not db_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found.",
            )

        db.delete(db_student)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to delete student with ID {student_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while deleting the student record.",
        )

