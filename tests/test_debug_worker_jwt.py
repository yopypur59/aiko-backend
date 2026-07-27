import base64
import json

from debug_worker_jwt import decode_jwt_payload, summarize_worker_jwt


def _token_with_payload(payload: dict[str, object]) -> str:
    encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    return f"header.{encoded}.signature"


def test_summarize_worker_jwt_exposes_only_safe_claims() -> None:
    token = _token_with_payload(
        {
            "iss": "API_example_key",
            "exp": 1_800_000_000,
            "aud": "livekit",
            "video": {"agent": True, "roomJoin": False},
            "sensitive": "must-not-be-logged",
        }
    )

    summary = summarize_worker_jwt(token)

    assert summary == {
        "iss": "API_example_key",
        "exp": 1_800_000_000,
        "aud": "livekit",
        "video_agent": True,
    }
    assert "signature" not in json.dumps(summary)
    assert "must-not-be-logged" not in json.dumps(summary)


def test_decode_jwt_payload_rejects_malformed_token() -> None:
    try:
        decode_jwt_payload("not-a-jwt")
    except ValueError as error:
        assert "three segments" in str(error)
    else:
        raise AssertionError("malformed JWT must be rejected")
