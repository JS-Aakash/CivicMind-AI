import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_command_center_overview():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/command-center/overview")
        assert res.status_code == 200
        data = res.json()
        assert "kpis" in data
        assert "critical_alerts" in data
        assert "emerging_incidents" in data
        assert "system_status" in data
        assert data["kpis"]["total_complaints"] >= 1000
        assert data["system_status"]["overall"] == "OPERATIONAL"


@pytest.mark.asyncio
async def test_analytics_summary_and_trends():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.get("/api/analytics/summary?timeframe=7d")
        assert res1.status_code == 200
        assert res1.json()["timeframe"] == "7d"
        assert res1.json()["sla_compliance_rate"] > 80.0

        res2 = await client.get("/api/analytics/trends?days=7")
        assert res2.status_code == 200
        assert len(res2.json()["trends"]) == 7

        res3 = await client.get("/api/analytics/categories")
        assert res3.status_code == 200
        assert len(res3.json()["categories"]) >= 4

        res4 = await client.get("/api/analytics/languages")
        assert res4.status_code == 200
        assert any(l["language"] == "Tamil" for l in res4.json()["languages"])


@pytest.mark.asyncio
async def test_review_queue_and_decision_feedback():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch review queue
        q_res = await client.get("/api/review/queue")
        assert q_res.status_code == 200
        queue_items = q_res.json()["items"]
        assert len(queue_items) > 0
        test_case = queue_items[0]

        # 2. Submit officer override decision
        decision_payload = {
            "action": "modify",
            "category": "drainage",
            "priority": "critical",
            "department_name": "Drainage & Stormwater Management",
            "sla_hours": 12,
            "officer_name": "Test Officer (Module 6 Test)",
            "reason": "Severe overflow into hospital entrance",
        }
        dec_res = await client.post(f"/api/review/{test_case['id']}/decision", json=decision_payload)
        assert dec_res.status_code == 200
        assert dec_res.json()["status"] == "success"

        # 3. Verify feedback record created
        fb_res = await client.get("/api/feedback")
        assert fb_res.status_code == 200
        feedbacks = fb_res.json()["items"]
        assert any(f["officer_name"] == "Test Officer (Module 6 Test)" for f in feedbacks)

        # 4. Verify audit event logged
        aud_res = await client.get("/api/audit")
        assert aud_res.status_code == 200
        events = aud_res.json()["events"]
        assert any("Test Officer" in ev["actor"] for ev in events)


@pytest.mark.asyncio
async def test_system_health_telemetry():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/system/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ALL_SYSTEMS_OPERATIONAL"
        assert len(data["components"]) >= 4
        comp_names = [c["id"] for c in data["components"]]
        assert "muril" in comp_names
        assert "whisper" in comp_names
        assert "incident_engine" in comp_names
