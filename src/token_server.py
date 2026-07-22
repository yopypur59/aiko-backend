import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from livekit import api
from pydantic import BaseModel

load_dotenv(".env.local")

app = FastAPI(
    title="LiveKit Token Server",
    version="1.0.0",
)


class TokenRequest(BaseModel):
    participant_name: str
    room_name: str


@app.get("/")
async def root():
    return {"message": "LiveKit Token Server is running"}


@app.post("/get-token")
async def get_token(request: TokenRequest):
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([livekit_url, api_key, api_secret]):
        raise HTTPException(
            status_code=500,
            detail="LiveKit environment variables are missing.",
        )

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(request.participant_name)
        .with_name(request.participant_name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=request.room_name,
            )
        )
        .to_jwt()
    )

    return {
        "serverUrl": livekit_url,
        "token": token,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "token_server:app",
        host=host,
        port=port,
        reload=True,
    )
