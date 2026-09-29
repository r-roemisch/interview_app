import base64
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from interview_app import db as db_module
from interview_app.images import OpenRouterImageClient, placeholder_png
from interview_app.llm import LLMUnavailable
from interview_app.main import create_app
from interview_app.models import Interview, Portrait, PortraitStatus

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})


def _start(client, llm, **overrides) -> dict:
    llm.responses += [PERSONA, "Hi, I'm Priya. Tell me about a project you led."]
    body = {"title": "Backend Engineer", "industry": "Fintech"} | overrides
    r = client.post("/interviews", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_portrait_is_pending_at_start_then_ready_and_served(client, llm, images):
    iv = _start(client, llm)
    assert iv["portrait"] == "pending"  # the response does not wait for the image

    # TestClient runs the background task right after the response.
    assert client.get(f"/interviews/{iv['id']}").json()["portrait"] == "ready"
    r = client.get(f"/interviews/{iv['id']}/portrait")
    assert (r.status_code, r.headers["content-type"], r.content) == (200, "image/png", images.image)


def test_no_portrait_when_switched_off(client, llm, images):
    iv = _start(client, llm, portrait=False)
    assert iv["portrait"] == "none"
    assert client.get(f"/interviews/{iv['id']}/portrait").status_code == 404
    assert images.prompts == []


def test_one_failure_is_tried_again(client, llm, images):
    images.errors = [LLMUnavailable("refused")]
    iv = _start(client, llm)
    assert client.get(f"/interviews/{iv['id']}").json()["portrait"] == "ready"
    assert len(images.prompts) == 2


def test_two_failures_leave_initials_and_the_interview_untouched(client, llm, images):
    images.errors = [LLMUnavailable("down"), LLMUnavailable("down")]
    iv = _start(client, llm)
    after = client.get(f"/interviews/{iv['id']}").json()
    assert after["portrait"] == "failed"
    assert (after["status"], len(after["messages"])) == ("in_progress", 1)
    assert client.get(f"/interviews/{iv['id']}/portrait").status_code == 404


def test_prompt_fits_the_persona_and_never_sees_cv_or_job_description(client, llm, images):
    _start(client, llm, cv="SECRET CV TEXT", job_description="SECRET JOB AD at Acme Corp")
    prompt = images.prompts[0]
    for expected in ("fictional woman", "Priya Nair", "Head of Engineering", "Fintech"):  # coral is female-sounding
        assert expected in prompt
    assert "SECRET" not in prompt and "Acme" not in prompt


def test_practice_again_copies_the_switch_and_makes_a_new_portrait(client, llm, images):
    with_portrait = _start(client, llm)
    without = _start(client, llm, portrait=False)

    llm.responses += [json.dumps({"name": "Tom Berg", "title": "VP Engineering", "voice": "ash"}), "Hi, I'm Tom. Q1?"]
    again = client.post(f"/interviews/{with_portrait['id']}/practice-again").json()
    assert client.get(f"/interviews/{again['id']}").json()["portrait"] == "ready"
    assert "fictional man named Tom Berg" in images.prompts[-1]

    llm.responses += [PERSONA, "Hi. Q1?"]
    assert client.post(f"/interviews/{without['id']}/practice-again").json()["portrait"] == "none"


def test_deleting_an_interview_deletes_its_portrait(client, llm, db):
    iv = _start(client, llm)
    assert client.delete(f"/interviews/{iv['id']}").status_code == 204
    assert db.query(Portrait).count() == 0


def test_startup_turns_unfinished_portraits_into_failed(engine, db, monkeypatch):
    # A server restart loses the background task; without this the shimmer would never stop.
    interview = Interview(title="PM", portrait=Portrait(status=PortraitStatus.PENDING))
    db.add(interview)
    db.commit()

    monkeypatch.setattr(db_module, "engine", engine)
    with TestClient(create_app()):
        pass

    db.expire_all()
    assert db.get(Interview, interview.id).portrait.status == PortraitStatus.FAILED


def _reply(images: list) -> SimpleNamespace:
    """A chat completion as the SDK returns it: the generated images are dicts on the message."""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Here it is:", images=images))])


def test_openrouter_client_asks_for_an_image_and_decodes_the_png(monkeypatch):
    client = OpenRouterImageClient("key", "image/model", sleep=lambda s: None)
    png = placeholder_png(4)
    seen = {}

    def fake_create(**kwargs):
        seen.update(kwargs)
        return _reply([{"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}])

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    assert client.portrait("A headshot") == png
    assert (seen["model"], seen["modalities"]) == ("image/model", ["image", "text"])


def test_openrouter_client_accepts_jpeg_and_serves_it_with_its_type(monkeypatch, client, llm, images):
    jpeg = b"\xff\xd8\xff\xe0 fake jpeg"
    images.image = jpeg
    iv = _start(client, llm)
    r = client.get(f"/interviews/{iv['id']}/portrait")
    assert (r.headers["content-type"], r.content) == ("image/jpeg", jpeg)


def test_openrouter_client_treats_a_reply_without_png_as_unavailable(monkeypatch):
    client = OpenRouterImageClient("key", "image/model", sleep=lambda s: None)
    monkeypatch.setattr(client._client.chat.completions, "create", lambda **kw: _reply([]))
    with pytest.raises(LLMUnavailable, match="no image: 'Here it is:'"):  # the model's text, for the log
        client.portrait("A headshot")
