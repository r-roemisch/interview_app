import json

from interview_app.llm import LLMUnavailable


def test_happy_path(client, llm):
    llm.responses.append(json.dumps({"title": "Data Engineer", "industry": "E-commerce", "seniority": "senior"}))
    r = client.post("/recommend-settings", json={"job_description": "We need a senior data engineer..."})
    assert r.status_code == 200, r.text
    assert r.json() == {"title": "Data Engineer", "industry": "E-commerce", "seniority": "senior"}
    assert "<job_description>" in llm.calls[0]["messages"][1]["content"]
    assert llm.calls[0]["json_schema"]["title"] == "RecommendedSettings"


def test_unknown_seniority_becomes_mid_and_blank_industry_is_null(client, llm):
    llm.responses.append("```json\n" + json.dumps({"title": "Lead PM", "industry": "", "seniority": "Lead"}) + "\n```")
    r = client.post("/recommend-settings", json={"job_description": "Lead product manager wanted"})
    assert r.status_code == 200
    assert r.json() == {"title": "Lead PM", "industry": None, "seniority": "mid"}


def test_seniority_prefix_match(client, llm):
    llm.responses.append(json.dumps({"title": "Dev", "industry": None, "seniority": "Mid-level"}))
    assert client.post("/recommend-settings", json={"job_description": "x"}).json()["seniority"] == "mid"


def test_empty_description_rejected_without_llm_call(client, llm):
    r = client.post("/recommend-settings", json={"job_description": "   "})
    assert r.status_code == 400
    assert llm.calls == []


def test_unparsable_twice_is_502(client, llm):
    llm.responses += ["not json", json.dumps({"industry": "x"})]  # second lacks title
    r = client.post("/recommend-settings", json={"job_description": "something"})
    assert r.status_code == 502
    assert len(llm.calls) == 2


def test_llm_unavailable_is_503(client, llm):
    llm.responses.append(LLMUnavailable("down"))
    assert client.post("/recommend-settings", json={"job_description": "something"}).status_code == 503
