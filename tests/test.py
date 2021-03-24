from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

# Test endpoint
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "Clubs API"

# Create A Club
def test_create_club():
    response = client.post(
        "/clubs",
        headers={"accept": "application/json", "Content-Type": "application/json"},
        json={"name": "Fenerbahce","country": "Turkey","established": 1907},
    )
    assert response.status_code == 200
    assert response.json() == {
        "name": "Fenerbahce",
        "country": "Turkey",
        "established": 1907,
    }

# Divide by zero error
def test_create_invalid_establish_date():
    response = client.post(
        "/clubs",
        headers={"accept": "application/json", "Content-Type": "application/json"},
        json={"name": "Fenerbahce","country": "Turkey","established": 0},
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json() == "An error occured while creating club"

# Provide invalid type value
def test_create_invalid_established_type():
    response = client.post(
        "/clubs",
        headers={"accept": "application/json", "Content-Type": "application/json"},
        json={"name": "Fenerbahce","country": "Turkey","established": "a"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail":[{"loc":["body","established"],"msg":"value is not a valid integer","type":"type_error.integer"}]}


# delete item
def test_delete_item():
    response = client.delete(
        "/clubs/Fenerbahce",
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200

# non-existed item
def test_delete_nonexist_item():
    response = client.delete(
        "/clubs/Chelsea",
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200
    assert response.json() == "An error occured while deleting club id:[], Chelsea"

# Test generating custom metrics
def test_log_custom_metric():
    response = client.get("/log_custom_metric")
    assert response.status_code == 200
    assert response.json() == "Log custom metric"
