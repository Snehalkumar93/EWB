import pytest
from app.database import get_session
from app.models import Student


@pytest.fixture(autouse=True)
def clean_students_table():
    """Ensure each read test starts with a clean, known database state."""
    db = get_session()
    db.query(Student).delete()
    db.commit()
    db.close()
    yield


def test_empty_database_returns_empty_list(test_client):
    """1. Verify empty database returns HTTP 200 and empty list []."""
    response = test_client.get("/students")
    assert response.status_code == 200
    assert response.json() == []


def test_single_student_appears_in_response(test_client):
    """2. Verify a single student appears in GET /students response."""
    test_client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14"},
    )
    response = test_client.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Aarav Sharma"


def test_multiple_students_returned(test_client):
    """3. Verify multiple created students are returned in GET /students."""
    students = [
        {"name": "Aarav Sharma", "date_of_birth": "2002-05-14"},
        {"name": "Diya Patel", "date_of_birth": "2003-01-22"},
        {"name": "Rohan Verma", "date_of_birth": "2001-11-09"},
    ]
    for s in students:
        test_client.post("/students", json=s)

    response = test_client.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_response_contains_all_expected_student_fields(test_client):
    """4. Verify response contains all expected fields for each student."""
    payload = {
        "name": "Ananya Gupta",
        "date_of_birth": "2002-09-15",
        "email": "ananya.gupta@example.com",
        "phone": "9876543210",
        "course": "Artificial Intelligence",
        "address": "456 IT Park, Hyderabad",
        "enrollment_date": "2024-08-01",
    }
    test_client.post("/students", json=payload)

    response = test_client.get("/students")
    assert response.status_code == 200
    student = response.json()[0]

    expected_keys = {
        "student_id",
        "name",
        "date_of_birth",
        "email",
        "phone",
        "course",
        "address",
        "enrollment_date",
    }
    assert expected_keys.issubset(student.keys())
    assert student["name"] == "Ananya Gupta"
    assert student["email"] == "ananya.gupta@example.com"
    assert student["course"] == "Artificial Intelligence"


def test_results_ordered_by_student_id_ascending(test_client):
    """5. Verify GET /students results are ordered by student_id ascending."""
    for name in ["Student A", "Student B", "Student C"]:
        test_client.post(
            "/students",
            json={"name": name, "date_of_birth": "2002-01-01"},
        )

    response = test_client.get("/students")
    assert response.status_code == 200
    ids = [s["student_id"] for s in response.json()]
    assert ids == sorted(ids)
    assert len(ids) == 3


def test_name_filtering_exact(test_client):
    """6. Verify name filtering returns matching records."""
    test_client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14"})
    test_client.post("/students", json={"name": "Diya Patel", "date_of_birth": "2003-01-22"})

    response = test_client.get("/students", params={"name": "Aarav Sharma"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Aarav Sharma"


def test_name_filtering_case_insensitive_and_partial(test_client):
    """7. Verify name filtering is case-insensitive and supports partial matching."""
    test_client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14"})
    test_client.post("/students", json={"name": "Kavya Sharma", "date_of_birth": "2003-03-10"})
    test_client.post("/students", json={"name": "Rohan Verma", "date_of_birth": "2001-11-09"})

    # Partial match 'sharma' in lowercase
    response = test_client.get("/students", params={"name": "sharma"})
    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert len(names) == 2
    assert "Aarav Sharma" in names
    assert "Kavya Sharma" in names

    # Uppercase partial match 'AARAV'
    response2 = test_client.get("/students", params={"name": "AARAV"})
    assert response2.status_code == 200
    assert len(response2.json()) == 1
    assert response2.json()[0]["name"] == "Aarav Sharma"


def test_course_filtering_exact(test_client):
    """8. Verify course filtering returns matching records."""
    test_client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14", "course": "Computer Science"},
    )
    test_client.post(
        "/students",
        json={"name": "Diya Patel", "date_of_birth": "2003-01-22", "course": "Mechanical"},
    )

    response = test_client.get("/students", params={"course": "Computer Science"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["course"] == "Computer Science"


def test_course_filtering_case_insensitive_and_partial(test_client):
    """9. Verify course filtering is case-insensitive and supports partial matching."""
    test_client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14", "course": "Computer Science"},
    )
    test_client.post(
        "/students",
        json={"name": "Diya Patel", "date_of_birth": "2003-01-22", "course": "Data Science"},
    )
    test_client.post(
        "/students",
        json={"name": "Rohan Verma", "date_of_birth": "2001-11-09", "course": "Civil Engineering"},
    )

    # Partial match 'science' in lowercase
    response = test_client.get("/students", params={"course": "science"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    courses = [s["course"] for s in data]
    assert "Computer Science" in courses
    assert "Data Science" in courses


def test_date_of_birth_filtering(test_client):
    """10. Verify exact date-of-birth filtering works."""
    test_client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14"})
    test_client.post("/students", json={"name": "Diya Patel", "date_of_birth": "2003-01-22"})

    response = test_client.get("/students", params={"date_of_birth": "2002-05-14"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["date_of_birth"] == "2002-05-14"
    assert data[0]["name"] == "Aarav Sharma"


def test_multiple_filters_combined(test_client):
    """11. Verify multiple filters can be combined together."""
    test_client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14", "course": "Computer Science"},
    )
    test_client.post(
        "/students",
        json={"name": "Aarav Verma", "date_of_birth": "2002-05-14", "course": "Mechanical"},
    )
    test_client.post(
        "/students",
        json={"name": "Diya Patel", "date_of_birth": "2003-01-22", "course": "Computer Science"},
    )

    response = test_client.get(
        "/students",
        params={"name": "aarav", "course": "computer", "date_of_birth": "2002-05-14"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Aarav Sharma"


def test_filters_matching_no_records_return_empty_list(test_client):
    """12. Verify filters matching no records return HTTP 200 and []."""
    test_client.post("/students", json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14"})

    response = test_client.get("/students", params={"name": "NonExistentStudent"})
    assert response.status_code == 200
    assert response.json() == []


def test_invalid_date_query_param_rejected(test_client):
    """13. Verify invalid date input in date_of_birth filter returns HTTP 422."""
    response = test_client.get("/students", params={"date_of_birth": "invalid-date"})
    assert response.status_code == 422


def test_get_student_by_id_success(test_client):
    """14. Verify an existing student can be retrieved by their student_id."""
    create_res = test_client.post(
        "/students",
        json={
            "name": "Meera Iyer",
            "date_of_birth": "2002-06-20",
            "email": "meera.iyer@example.com",
            "course": "Biotechnology",
        },
    )
    assert create_res.status_code == 201
    student_id = create_res.json()["student_id"]

    get_res = test_client.get(f"/students/{student_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["student_id"] == student_id
    assert data["name"] == "Meera Iyer"
    assert data["course"] == "Biotechnology"


def test_get_student_by_id_not_found(test_client):
    """15. Verify requesting a non-existent student ID returns HTTP 404 with clear message."""
    response = test_client.get("/students/999999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
    assert "999999" in data["detail"]


def test_get_student_by_id_zero_or_negative_rejected(test_client):
    """16. Verify zero and negative IDs are rejected with HTTP 422."""
    res_zero = test_client.get("/students/0")
    assert res_zero.status_code == 422

    res_negative = test_client.get("/students/-5")
    assert res_negative.status_code == 422


def test_returned_student_by_id_values_match_database(test_client):
    """17. Verify returned values for GET /students/{id} match the stored database record."""
    payload = {
        "name": "Siddharth Rao",
        "date_of_birth": "2001-04-18",
        "email": "siddharth.rao@example.com",
        "phone": "9876543299",
        "course": "Electrical Engineering",
        "address": "12 Lotus Lane, Chennai",
        "enrollment_date": "2024-08-05",
    }
    create_res = test_client.post("/students", json=payload)
    student_id = create_res.json()["student_id"]

    # Retrieve through API
    get_res = test_client.get(f"/students/{student_id}")
    assert get_res.status_code == 200
    api_data = get_res.json()

    # Query directly from DB
    db = get_session()
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    assert db_student is not None
    assert api_data["name"] == db_student.name
    assert api_data["date_of_birth"] == db_student.date_of_birth
    assert api_data["email"] == db_student.email
    assert api_data["phone"] == db_student.phone
    assert api_data["course"] == db_student.course
    assert api_data["address"] == db_student.address
    assert api_data["enrollment_date"] == db_student.enrollment_date
    db.close()
