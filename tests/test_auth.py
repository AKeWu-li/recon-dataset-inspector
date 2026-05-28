def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin",
            "password": "test123456"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "admin"
    assert data["is_active"] is True
    assert "hashed_password" not in data


def test_register_duplicate_username(client):
    response_1 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin",
            "password": "test123456"
        }
    )

    assert response_1.status_code == 200

    response_2 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin",
            "password": "test123456"
        }
    )

    assert response_2.status_code == 400


def test_login_user(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin",
            "password": "test123456"
        }
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin",
            "password": "test123456"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin",
            "password": "test123456"
        }
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401