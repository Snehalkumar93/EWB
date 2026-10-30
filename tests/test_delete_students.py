import pytest
from app.database import get_session
from app.models import Student


@pytest.fixture(autouse=True)
def clean_students_table():
    """Ensure each delete test starts with a clean database state."""
    db = get_session()
    db.query(Student).delete()
    db.commit()
    db.close()
    yield


def test_delete_student_success_status_code_204(test_client):
    """1. Verify successful deletion returns HTTP 204."""
    create_res = test_client.post(
        "/students",
        json={"name": "Aarav Sharma", "date_of_birth": "2002-05-14"},
    )
    assert create_res.status_code == 201
    student_id = create_res.json()["student_id"]

    delete_res = test_client.delete(f"/students/{student_id}")
    assert delete_res.status_code == 204


def test_delete_student_empty_response_body(test_client):
    """2. Verify successful deletion returns an empty response body."""
    create_res = test_client.post(
        "/students",
        json={"name": "Diya Patel", "date_of_birth": "2003-01-22"},
    )
    student_id = create_res.json()["student_id"]

    delete_res = test_client.delete(f"/students/{student_id}")
    assert delete_res.status_code == 204
    assert delete_res.content == b""
    assert len(delete_res.text) == 0


def test_deleted_student_no_longer_retrievable_via_get(test_client):
    """3. Verify the deleted student can no longer be retrieved via GET /students/{id}."""
    create_res = test_client.post(
        "/students",
        json={"name": "Rohan Verma", "date_of_birth": "2001-11-09"},
    )
    student_id = create_res.json()["student_id"]

    # Verify student exists first
    assert test_client.get(f"/students/{student_id}").status_code == 200

    # Delete student
    assert test_client.delete(f"/students/{student_id}").status_code == 204

    # Verify student returns 404
    get_res = test_client.get(f"/students/{student_id}")
    assert get_res.status_code == 404
    assert "not found" in get_res.json()["detail"].lower()


def test_delete_nonexistent_student_returns_404(test_client):
    """4. Verify deleting a nonexistent student returns HTTP 404."""
    delete_res = test_client.delete("/students/999999")
    assert delete_res.status_code == 404
    assert "not found" in delete_res.json()["detail"].lower()


def test_delete_same_student_twice_returns_204_then_404(test_client):
    """5. Verify deleting the same student twice returns 204 on first and 404 on second."""
    create_res = test_client.post(
        "/students",
        json={"name": "Ananya Gupta", "date_of_birth": "2002-09-15"},
    )
    student_id = create_res.json()["student_id"]

    # First delete returns 204
    res1 = test_client.delete(f"/students/{student_id}")
    assert res1.status_code == 204

    # Repeated delete returns 404
    res2 = test_client.delete(f"/students/{student_id}")
    assert res2.status_code == 404
    assert "not found" in res2.json()["detail"].lower()


def test_delete_zero_and_negative_ids_rejected_with_422(test_client):
    """6. Verify invalid IDs (0 and negative integers) return HTTP 422."""
    assert test_client.delete("/students/0").status_code == 422
    assert test_client.delete("/students/-1").status_code == 422
    assert test_client.delete("/students/-100").status_code == 422


def test_deleting_one_student_does_not_delete_others(test_client):
    """7. Verify deleting one student preserves all other student records."""
    res_a = test_client.post(
        "/students", json={"name": "Student A", "date_of_birth": "2002-01-01"}
    )
    res_b = test_client.post(
        "/students", json={"name": "Student B", "date_of_birth": "2002-02-02"}
    )
    res_c = test_client.post(
        "/students", json={"name": "Student C", "date_of_birth": "2002-03-03"}
    )

    id_a = res_a.json()["student_id"]
    id_b = res_b.json()["student_id"]
    id_c = res_c.json()["student_id"]

    # Delete Student B only
    assert test_client.delete(f"/students/{id_b}").status_code == 204

    # Check Student B is 404
    assert test_client.get(f"/students/{id_b}").status_code == 404

    # Check Student A and C still exist
    assert test_client.get(f"/students/{id_a}").status_code == 200
    assert test_client.get(f"/students/{id_c}").status_code == 200

    # Check GET /students list has exactly 2 records
    list_res = test_client.get("/students")
    assert list_res.status_code == 200
    remaining_ids = [s["student_id"] for s in list_res.json()]
    assert remaining_ids == [id_a, id_c]


def test_deletion_persists_in_database(test_client):
    """8. Verify the deletion is committed and persists in the SQLite database."""
    create_res = test_client.post(
        "/students",
        json={"name": "Kavya Nair", "date_of_birth": "2003-03-10"},
    )
    student_id = create_res.json()["student_id"]

    # Delete student via API
    assert test_client.delete(f"/students/{student_id}").status_code == 204

    # Query directly from database session
    db = get_session()
    record = db.query(Student).filter(Student.student_id == student_id).first()
    assert record is None
    db.close()


def test_existing_endpoints_work_after_deletion(test_client):
    """9. Verify existing GET, POST, PUT, and PATCH endpoints continue to function properly."""
    # POST
    c_res = test_client.post(
        "/students",
        json={"name": "Vikram Malhotra", "date_of_birth": "2001-08-19"},
    )
    assert c_res.status_code == 201
    sid = c_res.json()["student_id"]

    # PUT
    put_res = test_client.put(
        f"/students/{sid}",
        json={"name": "Vikram M.", "date_of_birth": "2001-08-19", "course": "Design"},
    )
    assert put_res.status_code == 200
    assert put_res.json()["course"] == "Design"

    # PATCH
    patch_res = test_client.patch(
        f"/students/{sid}",
        json={"course": "Architecture"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["course"] == "Architecture"

    # GET
    get_res = test_client.get(f"/students/{sid}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Vikram M."

    # DELETE
    del_res = test_client.delete(f"/students/{sid}")
    assert del_res.status_code == 204

    # Final GET confirms deletion
    assert test_client.get(f"/students/{sid}").status_code == 404
