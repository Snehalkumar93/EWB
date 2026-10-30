import pytest
from app.database import get_session
from app.models import Student


@pytest.fixture(autouse=True)
def clean_students_table():
    """Ensure each update test starts with a clean database state."""
    db = get_session()
    db.query(Student).delete()
    db.commit()
    db.close()
    yield


# ==========================================
# PUT /students/{student_id} Tests (1 - 8)
# ==========================================


def test_put_replace_all_fields_successfully(test_client):
    """1. Replace all editable fields successfully using PUT."""
    create_res = test_client.post(
        "/students",
        json={
            "name": "Initial Name",
            "date_of_birth": "2000-01-01",
            "email": "initial@example.com",
            "phone": "1111111111",
            "course": "Initial Course",
            "address": "Initial Address",
            "enrollment_date": "2023-01-01",
        },
    )
    assert create_res.status_code == 201
    student_id = create_res.json()["student_id"]

    put_payload = {
        "name": "Updated Name",
        "date_of_birth": "2002-05-14",
        "email": "updated@example.com",
        "phone": "9876543210",
        "course": "Advanced Robotics",
        "address": "456 Silicon Valley, Bengaluru",
        "enrollment_date": "2024-08-01",
    }
    put_res = test_client.put(f"/students/{student_id}", json=put_payload)
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["student_id"] == student_id
    for key, val in put_payload.items():
        assert data[key] == val


def test_put_returns_updated_record_http_200(test_client):
    """2. Verify PUT returns HTTP 200 and updated student object."""
    create_res = test_client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14"},
    )
    student_id = create_res.json()["student_id"]

    put_payload = {
        "name": "Aarav S.",
        "date_of_birth": "2002-05-14",
        "course": "Computer Science",
    }
    put_res = test_client.put(f"/students/{student_id}", json=put_payload)
    assert put_res.status_code == 200
    assert put_res.json()["name"] == "Aarav S."
    assert put_res.json()["course"] == "Computer Science"


def test_put_missing_student_returns_404(test_client):
    """3. Verify PUT returns HTTP 404 for a missing student."""
    put_payload = {
        "name": "Ghost Student",
        "date_of_birth": "2002-05-14",
    }
    put_res = test_client.put("/students/999999", json=put_payload)
    assert put_res.status_code == 404
    assert "not found" in put_res.json()["detail"].lower()


def test_put_missing_required_fields_rejected(test_client):
    """4. Verify PUT rejects missing required fields (name, date_of_birth) with HTTP 422."""
    create_res = test_client.post(
        "/students",
        json={"name": "Diya Patel", "date_of_birth": "2003-01-22"},
    )
    student_id = create_res.json()["student_id"]

    # Missing name
    res1 = test_client.put(
        f"/students/{student_id}",
        json={"date_of_birth": "2003-01-22"},
    )
    assert res1.status_code == 422

    # Missing date_of_birth
    res2 = test_client.put(
        f"/students/{student_id}",
        json={"name": "Diya Patel"},
    )
    assert res2.status_code == 422


def test_put_invalid_email_and_date_rejected(test_client):
    """5. Verify PUT rejects invalid email and date formats with HTTP 422."""
    create_res = test_client.post(
        "/students",
        json={"name": "Rohan Verma", "date_of_birth": "2001-11-09"},
    )
    student_id = create_res.json()["student_id"]

    # Invalid email
    res1 = test_client.put(
        f"/students/{student_id}",
        json={
            "name": "Rohan Verma",
            "date_of_birth": "2001-11-09",
            "email": "not-a-valid-email",
        },
    )
    assert res1.status_code == 422

    # Invalid date
    res2 = test_client.put(
        f"/students/{student_id}",
        json={
            "name": "Rohan Verma",
            "date_of_birth": "11-09-2001",
        },
    )
    assert res2.status_code == 422


def test_put_empty_or_whitespace_name_rejected(test_client):
    """6. Verify PUT rejects empty or whitespace-only name with HTTP 422."""
    create_res = test_client.post(
        "/students",
        json={"name": "Kavya Nair", "date_of_birth": "2003-03-10"},
    )
    student_id = create_res.json()["student_id"]

    res_empty = test_client.put(
        f"/students/{student_id}",
        json={"name": "", "date_of_birth": "2003-03-10"},
    )
    assert res_empty.status_code == 422

    res_spaces = test_client.put(
        f"/students/{student_id}",
        json={"name": "    ", "date_of_birth": "2003-03-10"},
    )
    assert res_spaces.status_code == 422


def test_put_zero_or_negative_student_id_rejected(test_client):
    """7. Verify PUT rejects zero or negative student IDs with HTTP 422."""
    valid_payload = {"name": "Test Student", "date_of_birth": "2002-05-14"}
    assert test_client.put("/students/0", json=valid_payload).status_code == 422
    assert test_client.put("/students/-1", json=valid_payload).status_code == 422


def test_put_student_id_remains_unchanged(test_client):
    """8. Confirm student_id remains unchanged after PUT, and client attempts to send student_id are rejected."""
    create_res = test_client.post(
        "/students",
        json={"name": "Aditya Joshi", "date_of_birth": "2002-07-25"},
    )
    student_id = create_res.json()["student_id"]

    # Attempting to supply student_id in body must be rejected (extra field forbidden)
    put_with_id = {
        "student_id": 9999,
        "name": "Aditya Joshi",
        "date_of_birth": "2002-07-25",
    }
    res_tamper = test_client.put(f"/students/{student_id}", json=put_with_id)
    assert res_tamper.status_code == 422

    # Normal PUT preserves original student_id
    put_res = test_client.put(
        f"/students/{student_id}",
        json={"name": "Aditya J.", "date_of_birth": "2002-07-25"},
    )
    assert put_res.status_code == 200
    assert put_res.json()["student_id"] == student_id


# ==========================================
# PATCH /students/{student_id} Tests (9 - 18)
# ==========================================


def test_patch_update_only_name_preserves_other_fields(test_client):
    """9. Update only the name and preserve all other fields."""
    create_res = test_client.post(
        "/students",
        json={
            "name": "Original Name",
            "date_of_birth": "2002-05-14",
            "email": "original@example.com",
            "phone": "9876543210",
            "course": "Computer Science",
            "address": "123 Main St",
            "enrollment_date": "2024-08-01",
        },
    )
    student_id = create_res.json()["student_id"]

    patch_res = test_client.patch(
        f"/students/{student_id}",
        json={"name": "New Patched Name"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "New Patched Name"
    assert data["date_of_birth"] == "2002-05-14"
    assert data["email"] == "original@example.com"
    assert data["phone"] == "9876543210"
    assert data["course"] == "Computer Science"
    assert data["address"] == "123 Main St"
    assert data["enrollment_date"] == "2024-08-01"


def test_patch_update_only_course(test_client):
    """10. Update only the course field."""
    create_res = test_client.post(
        "/students",
        json={"name": "Diya Patel", "date_of_birth": "2003-01-22", "course": "Mechanical"},
    )
    student_id = create_res.json()["student_id"]

    patch_res = test_client.patch(
        f"/students/{student_id}",
        json={"course": "Mechatronics"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["course"] == "Mechatronics"
    assert patch_res.json()["name"] == "Diya Patel"


def test_patch_update_multiple_selected_fields(test_client):
    """11. Update multiple selected fields together."""
    create_res = test_client.post(
        "/students",
        json={
            "name": "Siddharth Rao",
            "date_of_birth": "2001-04-18",
            "course": "Electrical",
            "phone": "1111111111",
        },
    )
    student_id = create_res.json()["student_id"]

    patch_res = test_client.patch(
        f"/students/{student_id}",
        json={"course": "Electronics & Communication", "phone": "9998887776"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["course"] == "Electronics & Communication"
    assert data["phone"] == "9998887776"
    assert data["name"] == "Siddharth Rao"


def test_patch_preserve_omitted_fields(test_client):
    """12. Verify omitted fields are strictly preserved and not overwritten with None."""
    create_res = test_client.post(
        "/students",
        json={
            "name": "Meera Iyer",
            "date_of_birth": "2002-06-20",
            "email": "meera@example.com",
            "address": "42 Lake View",
        },
    )
    student_id = create_res.json()["student_id"]

    patch_res = test_client.patch(
        f"/students/{student_id}",
        json={"email": "meera.new@example.com"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["email"] == "meera.new@example.com"
    assert data["address"] == "42 Lake View"
    assert data["name"] == "Meera Iyer"


def test_patch_empty_request_rejected(test_client):
    """13. Reject an empty patch request with HTTP 422."""
    create_res = test_client.post(
        "/students",
        json={"name": "Test Student", "date_of_birth": "2002-05-14"},
    )
    student_id = create_res.json()["student_id"]

    patch_res = test_client.patch(f"/students/{student_id}", json={})
    assert patch_res.status_code == 422
    assert "at least one field" in patch_res.json()["detail"].lower()


def test_patch_invalid_email_and_date_rejected(test_client):
    """14. Reject invalid email and date values in PATCH with HTTP 422."""
    create_res = test_client.post(
        "/students",
        json={"name": "Test Student", "date_of_birth": "2002-05-14"},
    )
    student_id = create_res.json()["student_id"]

    # Invalid email
    res1 = test_client.patch(f"/students/{student_id}", json={"email": "bad-email"})
    assert res1.status_code == 422

    # Invalid date of birth
    res2 = test_client.patch(f"/students/{student_id}", json={"date_of_birth": "invalid-date"})
    assert res2.status_code == 422


def test_patch_missing_student_returns_404(test_client):
    """15. Return HTTP 404 for a nonexistent student on PATCH."""
    patch_res = test_client.patch(
        "/students/999999",
        json={"name": "Nonexistent Student"},
    )
    assert patch_res.status_code == 404
    assert "not found" in patch_res.json()["detail"].lower()


def test_patch_invalid_student_id_rejected(test_client):
    """16. Reject zero and negative student IDs on PATCH with HTTP 422."""
    assert test_client.patch("/students/0", json={"name": "Test"}).status_code == 422
    assert test_client.patch("/students/-10", json={"name": "Test"}).status_code == 422


def test_patch_reject_attempts_to_modify_student_id(test_client):
    """17. Reject attempts to modify student_id via PATCH with HTTP 422."""
    create_res = test_client.post(
        "/students",
        json={"name": "Pooja Reddy", "date_of_birth": "2003-12-05"},
    )
    student_id = create_res.json()["student_id"]

    # Sending student_id in PATCH payload must be forbidden
    tamper_res = test_client.patch(
        f"/students/{student_id}",
        json={"student_id": 12345, "name": "Pooja R."},
    )
    assert tamper_res.status_code == 422


def test_patch_updated_record_persists_in_database(test_client):
    """18. Confirm the updated record persists directly in SQLite database."""
    create_res = test_client.post(
        "/students",
        json={"name": "Tanvi Sen", "date_of_birth": "2002-08-30", "course": "Physics"},
    )
    student_id = create_res.json()["student_id"]

    patch_res = test_client.patch(
        f"/students/{student_id}",
        json={"course": "Astrophysics"},
    )
    assert patch_res.status_code == 200

    # Query directly from DB
    db = get_session()
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    assert db_student is not None
    assert db_student.course == "Astrophysics"
    assert db_student.name == "Tanvi Sen"
    db.close()
