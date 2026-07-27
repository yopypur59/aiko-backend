"""Temporary, safe JWT payload logger for LiveKit Agent Worker authentication.

Run this wrapper instead of ``agent.py`` once while investigating a `/agent` 401.
It never prints the JWT, its signature, or the API secret.
"""

from __future__ import annotations

import base64
import json
import runpy
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode a JWT payload without verifying or logging the credential itself."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("JWT must contain exactly three segments")

    payload_segment = parts[1]
    padded_payload = payload_segment + "=" * (-len(payload_segment) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded_payload))
    except (ValueError, json.JSONDecodeError) as error:
        raise ValueError("JWT payload is not valid base64url JSON") from error

    if not isinstance(payload, dict):
        raise ValueError("JWT payload must be a JSON object")
    return payload


def summarize_worker_jwt(token: str) -> dict[str, Any]:
    """Return only the non-secret worker-authentication claims required for debugging."""
    payload = decode_jwt_payload(token)
    video = payload.get("video")
    return {
        "iss": payload.get("iss"),
        "exp": payload.get("exp"),
        "aud": payload.get("aud"),
        "video_agent": video.get("agent") if isinstance(video, dict) else None,
    }


def _is_agent_websocket(url: object) -> bool:
    return urlparse(str(url)).path.rstrip("/").endswith("/agent")


def install_worker_jwt_logger() -> None:
    """Log the exact bearer JWT payload immediately before aiohttp opens `/agent`."""
    if getattr(aiohttp.ClientSession, "_livekit_jwt_debug_installed", False):
        return

    original_ws_connect = aiohttp.ClientSession.ws_connect

    # UNVERIFIED AGAINST LIVEKIT MCP: verified against installed livekit-agents 1.5.16.
    async def ws_connect_with_worker_jwt_log(
        session: aiohttp.ClientSession,
        url: object,
        *args: Any,
        **kwargs: Any,
    ) -> aiohttp.ClientWebSocketResponse:
        headers = kwargs.get("headers")
        if _is_agent_websocket(url) and isinstance(headers, Mapping):
            authorization = headers.get("Authorization")
            if isinstance(authorization, str) and authorization.startswith("Bearer "):
                try:
                    summary = summarize_worker_jwt(
                        authorization.removeprefix("Bearer ")
                    )
                except ValueError as error:
                    print(f"[livekit-worker-jwt] decode_error={error}", flush=True)
                else:
                    print(
                        "[livekit-worker-jwt] payload="
                        + json.dumps(summary, sort_keys=True),
                        flush=True,
                    )

        return await original_ws_connect(session, url, *args, **kwargs)

    aiohttp.ClientSession.ws_connect = ws_connect_with_worker_jwt_log
    aiohttp.ClientSession._livekit_jwt_debug_installed = True


def main() -> None:
    agent_file = Path(__file__).resolve().with_name("agent.py")
    if not agent_file.is_file():
        raise FileNotFoundError(f"Agent entrypoint not found: {agent_file}")

    install_worker_jwt_logger()
    sys.argv = [str(agent_file), *sys.argv[1:]]
    runpy.run_path(str(agent_file), run_name="__main__")


if __name__ == "__main__":
    main()
