"""End-to-end API tests for AI recommendations (candidate + owner)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_candidate_recommendations_happy_path(client: TestClient, candidate_token: dict):
    professional_id = candidate_token["professional_id"]
    res = client.post(
        "/api/agents/recommendations",
        json={
            "professional_id": professional_id,
            "mode": "candidate",
            "limit": 5,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["mode"] == "candidate"
    assert body["professional_id"] == professional_id
    assert body["source"] in {"heuristic", "openai"}
    assert isinstance(body["recommendations"], list)
    assert len(body["recommendations"]) <= 5
    if body["recommendations"]:
        top = body["recommendations"][0]
        assert "seat_id" in top
        assert "title" in top
        assert 0 <= top["match_score"] <= 1
        assert top["reason"]
        # Sorted descending
        scores = [r["match_score"] for r in body["recommendations"]]
        assert scores == sorted(scores, reverse=True)


def test_candidate_recommendations_unknown_profile(client: TestClient):
    res = client.post(
        "/api/agents/recommendations",
        json={"professional_id": "NOPE", "mode": "candidate"},
    )
    assert res.status_code == 404


def test_owner_recommendations_require_seat_id(client: TestClient):
    res = client.post(
        "/api/agents/recommendations",
        json={"professional_id": "MC2NVD9RTPW5", "mode": "owner"},
    )
    assert res.status_code == 400
    assert "seat_id" in res.json()["detail"].lower()


def test_owner_recommendations_unknown_seat(client: TestClient):
    res = client.post(
        "/api/agents/recommendations",
        json={
            "professional_id": "MC2NVD9RTPW5",
            "mode": "owner",
            "seat_id": "SEAT-DOES-NOT-EXIST",
        },
    )
    assert res.status_code == 404


def test_owner_recommendations_forbidden_for_non_owner(client: TestClient):
    # SEAT-001 is owned by Marcus (mchen), not Sarah
    res = client.post(
        "/api/agents/recommendations",
        json={
            "professional_id": "SW8FHK4TQNX7",
            "mode": "owner",
            "seat_id": "SEAT-001",
        },
    )
    assert res.status_code == 403


def test_owner_recommendations_ranks_only_in_play_applicants(client: TestClient):
    res = client.post(
        "/api/agents/recommendations",
        json={
            "professional_id": "MC2NVD9RTPW5",
            "mode": "owner",
            "seat_id": "SEAT-001",
            "limit": 20,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["mode"] == "owner"
    assert body["seat_id"] == "SEAT-001"
    assert body["recommendations"]
    ids = {r["professional_id"] for r in body["recommendations"]}
    # Seeded applicants for SEAT-001
    assert ids <= {"JS7BQM3PXWK1", "A5XCVSPCNN2O", "SW8FHK4TQNX7", "DR3KGP6LMZY8"}
    # Owner themselves should not appear as an applicant on their seat
    assert "MC2NVD9RTPW5" not in ids
    scores = [r["match_score"] for r in body["recommendations"]]
    assert scores == sorted(scores, reverse=True)


def test_owner_list_applicants_requires_auth(client: TestClient):
    res = client.get("/api/owner/listings/SEAT-001/applicants")
    assert res.status_code == 401


def test_owner_list_applicants_happy_path(client: TestClient, owner_token: str):
    res = client.get(
        "/api/owner/listings/SEAT-001/applicants",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["seat_id"] == "SEAT-001"
    assert body["total"] >= 1
    assert all("professional_id" in a for a in body["applicants"])


def test_owner_list_applicants_forbidden_for_other_owner(client: TestClient):
    login = client.post("/api/auth/login", json={"username": "swilliams", "password": "password"})
    token = login.json()["token"]
    res = client.get(
        "/api/owner/listings/SEAT-001/applicants",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_candidate_and_owner_flows_together(client: TestClient, candidate_token: dict, owner_token: str):
    """Smoke: candidate seat recs + owner applicant ranking in one session."""
    cand = client.post(
        "/api/agents/recommendations",
        json={
            "professional_id": candidate_token["professional_id"],
            "mode": "candidate",
            "limit": 3,
        },
    )
    assert cand.status_code == 200
    assert len(cand.json()["recommendations"]) <= 3

    applicants = client.get(
        "/api/owner/listings/SEAT-001/applicants",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert applicants.status_code == 200

    ranked = client.post(
        "/api/agents/recommendations",
        json={
            "professional_id": "MC2NVD9RTPW5",
            "mode": "owner",
            "seat_id": "SEAT-001",
        },
    )
    assert ranked.status_code == 200
    assert ranked.json()["recommendations"]
