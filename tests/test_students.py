import pytest
from app.database import get_session
from app.models import Student


def test_create_valid_student(test_client):
    """1. Verify a valid student can be created with HTTP 201."""
    payload = {
        "name": "Aarav Sharma",
        "date_of_birth": "2002-05-14",
        "email": "aarav.sharma@example.com",
        "phone": "9876543210",
        "course": "Computer Science",
        "address": "123 MG Road, Bengaluru",
        "enrollment_date": "2024-08-01",
    }
    response = test_client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "student_id" in data
    assert data["name"] == "Aarav Sharma"
    assert data["date_of_birth"] == "2002-05-14"
    assert data["email"] == "aarav.sharma@example.com"
    assert data["phone"] == "9876543210"
    assert data["course"] == "Computer Science"
    assert data["address"] == "123 MG Road, Bengaluru"
    assert data["enrollment_date"] == "2024-08-01"


def test_response_contains_generated_student_id(test_client):
    """2. Verify the response contains the generated student_id as an integer."""
    payload = {
        "name": "Diya Patel",
        "date_of_birth": "2003-01-22",
    }
    response = test_client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data["student_id"], int)
    assert data["student_id"] > 0


def test_returned_student_data_matches_submitted_data(test_client):
    """3. Verify the returned student data matches the submitted payload."""
    payload = {
        "name": "Rohan Verma",
        "date_of_birth": "2001-11-09",
        "email": "rohan.verma@example.com",
        "phone": "9876543212",
        "course": "Mechanical Engineering",
        "address": "789 Lake View, Pune",
        "enrollment_date": "2024-08-02",
    }
    response = test_client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    for key, val in payload.items():
        assert data[key] == val


def test_record_can_be_retrieved_directly_from_database(test_client):
    """4. Verify that the created student record can be retrieved directly from SQLite database."""
    payload = {
        "name": "Ananya Gupta",
        "date_of_birth": "2002-09-15",
        "email": "ananya.gupta@example.com",
        "course": "Artificial Intelligence",
    }
    response = test_client.post("/students", json=payload)
    assert response.status_code == 201
    created_id = response.json()["student_id"]

    # Directly query SQLite using a new database session
    db = get_session()
    db_student = db.query(Student).filter(Student.student_id == created_id).first()
    assert db_student is not None
    assert db_student.name == "Ananya Gupta"
    assert db_student.date_of_birth == "2002-09-15"
    assert db_student.email == "ananya.gupta@example.com"
    assert db_student.course == "Artificial Intelligence"
    db.close()


def test_multiple_students_receive_different_ids(test_client):
    """5. Verify that multiple students receive unique and distinct generated IDs."""
    payload1 = {
        "name": "Kavya Nair",
        "date_of_birth": "2003-03-10",
        "email": "kavya.nair@example.com",
    }
    payload2 = {
        "name": "Aditya Joshi",
        "date_of_birth": "2002-07-25",
        "email": "aditya.joshi@example.com",
    }

    res1 = test_client.post("/students", json=payload1)
    res2 = test_client.post("/students", json=payload2)

    assert res1.status_code == 201
    assert res2.status_code == 201
    id1 = res1.json()["student_id"]
    id2 = res2.json()["student_id"]
    assert id1 != id2


def test_missing_name_rejected(test_client):
    """6. Verify that omitting required field 'name' returns HTTP 422."""
    payload = {
        "date_of_birth": "2002-05-14",
        "email": "student@example.com",
    }
    response = test_client.post("/students", json=payload)
    assert response.status_code == 422


def test_missing_date_of_birth_rejected(test_client):
    """7. Verify that omitting required field 'date_of_birth' returns HTTP 422."""
    payload = {
        "name": "Siddharth Rao",
        "email": "siddharth@example.com",
    }
    response = test_client.post("/students", json=payload)
    assert response.status_code == 422


def test_invalid_email_rejected(test_client):
    """8. Verify that an invalid email string returns HTTP 422."""
    payload = {
        "name": "Pooja Reddy",
        "date_of_birth": "2003-12-05",
        "email": "invalid-email-address",
    }
    response = test_client.post("/students", json=payload)
    assert response.status_code == 422


def test_invalid_date_format_rejected(test_client):
    """9. Verify that an invalid date format returns HTTP 422."""
    # Invalid date of birth format
    payload1 = {
        "name": "Meera Iyer",
        "date_of_birth": "14-05-2002",  # Should be YYYY-MM-DD
    }
    response1 = test_client.post("/students", json=payload1)
    assert response1.status_code == 422

    # Nonexistent date
    payload2 = {
        "name": "Meera Iyer",
        "date_of_birth": "2024-02-31",
    }
    response2 = test_client.post("/students", json=payload2)
    assert response2.status_code == 422

    # Invalid enrollment date format
    payload3 = {
        "name": "Meera Iyer",
        "date_of_birth": "2002-05-14",
        "enrollment_date": "not-a-date",
    }
    response3 = test_client.post("/students", json=payload3)
    assert response3.status_code == 422


def test_empty_or_whitespace_name_rejected(test_client):
    """10. Verify that empty or whitespace-only name is rejected with HTTP 422."""
    # Empty string
    response_empty = test_client.post(
        "/students", json={"name": "", "date_of_birth": "2002-05-14"}
    )
    assert response_empty.status_code == 422

    # Whitespace only
    response_spaces = test_client.post(
        "/students", json={"name": "     ", "date_of_birth": "2002-05-14"}
    )
    assert response_spaces.status_code == 422


def test_optional_fields_can_be_omitted(test_client):
    """11. Verify that optional fields can be omitted and default to None."""
    payload = {
        "name": "Vikram Malhotra",
        "date_of_birth": "2001-08-19",
    }
    response = test_client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Vikram Malhotra"
    assert data["date_of_birth"] == "2001-08-19"
    assert data["email"] is None
    assert data["phone"] is None
    assert data["course"] is None
    assert data["address"] is None
    assert data["enrollment_date"] is None


def test_string_length_limits(test_client):
    """Verify that excessive field lengths are rejected with HTTP 422."""
    # Name exceeds 100 characters
    long_name = "A" * 101
    res1 = test_client.post(
        "/students", json={"name": long_name, "date_of_birth": "2002-05-14"}
    )
    assert res1.status_code == 422

    # Phone exceeds 20 characters
    long_phone = "1" * 21
    res2 = test_client.post(
        "/students",
        json={
            "name": "Tanvi Sen",
            "date_of_birth": "2002-05-14",
            "phone": long_phone,
        },
    )
    assert res2.status_code == 422
