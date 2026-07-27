import os
import random
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel

if os.path.exists(".env.local"):
    load_dotenv(".env.local")
load_dotenv()

app = FastAPI(
    title="LiveKit Token Server",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    participant_name: Optional[str] = None
    room_name: Optional[str] = None
    room_config: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    return {"message": "LiveKit Token Server is running"}


@app.post("/get-token")
async def get_token(request: Optional[TokenRequest] = None):
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([livekit_url, api_key, api_secret]):
        raise HTTPException(
            status_code=500,
            detail="LiveKit environment variables are missing.",
        )

    participant_name = (
        request.participant_name
        if request and request.participant_name
        else f"voice_assistant_user_{random.randint(1000, 9999)}"
    )
    room_name = (
        request.room_name
        if request and request.room_name
        else f"voice_assistant_room_{random.randint(1000, 9999)}"
    )

    grant = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    token_builder = (
        api.AccessToken(api_key, api_secret)
        .with_identity(participant_name)
        .with_name(participant_name)
        .with_grants(grant)
    )

    token = token_builder.to_jwt()

    return {
        "serverUrl": livekit_url,
        "roomName": room_name,
        "participantName": participant_name,
        "participantToken": token,
        "token": token,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "src.token_server:app",
        host=host,
        port=port,
        reload=True,
    )
