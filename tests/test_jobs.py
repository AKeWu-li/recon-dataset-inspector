def test_jobs_requires_auth(client):
    response = client.get("/api/v1/jobs/")

    assert response.status_code == 401


def test_create_job_with_auth_and_auto_run_false(client, auth_headers):
    response = client.post(
        "/api/v1/jobs/",
        headers=auth_headers,
        json={
            "input_path": "dataset/images",
            "output_path": "output/test_job",
            "blur_threshold": 50,
            "auto_run": False
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["input_path"] == "dataset/images"
    assert data["output_path"] == "output/test_job"
    assert data["blur_threshold"] == 50
    assert data["status"] in [
        "registered",
        "success",
        "after_colmap_success",
        "colmap_finished"
    ]


def test_list_jobs_with_auth(client, auth_headers):
    client.post(
        "/api/v1/jobs/",
        headers=auth_headers,
        json={
            "input_path": "dataset/images",
            "output_path": "output/test_job",
            "blur_threshold": 50,
            "auto_run": False
        }
    )

    response = client.get(
        "/api/v1/jobs/",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1