import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, text
from app.database import Base, init_db, get_session, get_engine
from app.models import Student


def test_database_connection_succeeds(temp_engine):
    """Verify that a connection to SQLite database succeeds."""
    with temp_engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_students_table_created(temp_engine):
    """Verify that init_db successfully creates the students table."""
    init_db(target_engine=temp_engine)
    inspector = inspect(temp_engine)
    tables = inspector.get_table_names()
    assert "students" in tables


def test_students_table_all_required_columns_exist(temp_engine):
    """Verify all required columns and constraints exist on students table:
    - student_id: INTEGER PRIMARY KEY AUTOINCREMENT
    - name: TEXT NOT NULL
    - date_of_birth: TEXT NOT NULL
    - email: TEXT
    - phone: TEXT
    - course: TEXT
    - address: TEXT
    - enrollment_date: TEXT
    """
    init_db(target_engine=temp_engine)
    inspector = inspect(temp_engine)
    columns = inspector.get_columns("students")
    column_dict = {col["name"]: col for col in columns}

    expected_columns = [
        "student_id",
        "name",
        "date_of_birth",
        "email",
        "phone",
        "course",
        "address",
        "enrollment_date",
    ]

    for col_name in expected_columns:
        assert col_name in column_dict, f"Missing required column: {col_name}"

    # Verify primary key and non-null constraints
    assert column_dict["student_id"]["primary_key"] == 1
    assert column_dict["name"]["nullable"] is False
    assert column_dict["date_of_birth"]["nullable"] is False
    assert column_dict["email"]["nullable"] is True


def test_student_id_automatically_generated_and_unique(temp_engine):
    """Verify student_id is automatically generated and unique for each record."""
    init_db(target_engine=temp_engine)
    session = get_session(target_engine=temp_engine)

    student1 = Student(
        name="Aarav Sharma",
        date_of_birth="2002-05-14",
        email="aarav.sharma@example.com",
    )
    student2 = Student(
        name="Diya Patel",
        date_of_birth="2003-01-22",
        email="diya.patel@example.com",
    )

    session.add(student1)
    session.add(student2)
    session.commit()

    assert student1.student_id is not None
    assert student2.student_id is not None
    assert student1.student_id != student2.student_id
    session.close()


def test_multiple_student_records_inserted_and_retrieved(temp_engine):
    """Verify inserting and querying multiple student records."""
    init_db(target_engine=temp_engine)
    session = get_session(target_engine=temp_engine)

    records = [
        Student(
            name="Aarav Sharma",
            date_of_birth="2002-05-14",
            email="aarav@example.com",
            phone="9876543210",
            course="Computer Science",
            address="123 MG Road, Bengaluru",
            enrollment_date="2024-08-01",
        ),
        Student(
            name="Diya Patel",
            date_of_birth="2003-01-22",
            email="diya@example.com",
            phone="9876543211",
            course="Data Science",
            address="456 Park Street, Mumbai",
            enrollment_date="2024-08-01",
        ),
        Student(
            name="Rohan Verma",
            date_of_birth="2001-11-09",
            email="rohan@example.com",
            phone="9876543212",
            course="Mechanical Engineering",
            address="789 Lake View, Pune",
            enrollment_date="2024-08-02",
        ),
    ]

    session.add_all(records)
    session.commit()

    retrieved = session.query(Student).order_by(Student.student_id).all()
    assert len(retrieved) == 3
    assert retrieved[0].name == "Aarav Sharma"
    assert retrieved[1].course == "Data Science"
    assert retrieved[2].phone == "9876543212"
    session.close()


def test_data_persists_after_closing_and_reopening(temp_db_file):
    """Verify that records persist in SQLite file after closing and reopening connection."""
    db_url = f"sqlite:///{temp_db_file}"

    # First session: initialize and insert
    engine_1 = create_engine(db_url, connect_args={"check_same_thread": False})
    init_db(target_engine=engine_1)
    session_1 = get_session(target_engine=engine_1)

    student = Student(
        name="Ananya Gupta",
        date_of_birth="2002-09-15",
        email="ananya.gupta@example.com",
        course="Artificial Intelligence",
    )
    session_1.add(student)
    session_1.commit()
    inserted_id = student.student_id
    session_1.close()
    engine_1.dispose()

    # Second session: reconnect with a completely new engine and verify persistence
    engine_2 = create_engine(db_url, connect_args={"check_same_thread": False})
    session_2 = get_session(target_engine=engine_2)
    loaded_student = session_2.query(Student).filter(Student.student_id == inserted_id).first()

    assert loaded_student is not None
    assert loaded_student.name == "Ananya Gupta"
    assert loaded_student.course == "Artificial Intelligence"
    assert loaded_student.email == "ananya.gupta@example.com"
    session_2.close()
    engine_2.dispose()


def test_database_initialization_idempotent(temp_engine):
    """Verify init_db can run multiple times without throwing errors or corrupting schema."""
    init_db(target_engine=temp_engine)
    init_db(target_engine=temp_engine)
    init_db(target_engine=temp_engine)

    inspector = inspect(temp_engine)
    assert "students" in inspector.get_table_names()


def test_fastapi_startup_initializes_database(test_client):
    """Verify that starting FastAPI application via lifespan automatically initializes the database."""
    response = test_client.get("/health")
    assert response.status_code == 200

    # Verify tables exist on the active database engine
    active_engine = get_engine()
    inspector = inspect(active_engine)
    assert "students" in inspector.get_table_names()


def test_no_production_database_file_created():
    """Verify that automated tests do not create or touch real project students.db."""
    project_db_path = Path("students.db")
    assert not project_db_path.exists(), "students.db should not exist in workspace root during test runs"
