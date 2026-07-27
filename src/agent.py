import asyncio
import logging
import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    room_io,
)
from livekit.plugins import google

from transcript_store import save_transcript

if os.path.exists(".env.local"):
    load_dotenv(".env.local")
load_dotenv()

logger = logging.getLogger(__name__)


def get_instructions() -> str:
    file_path = os.path.join(os.path.dirname(__file__), "instructions.txt")
    with open(file_path, encoding="utf-8") as file:
        return file.read().strip()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=get_instructions(),
        )


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            voice="Aoede",
            temperature=0.6,
        )
    )

    @ctx.add_shutdown_callback
    async def on_shutdown(reason: str):
        messages = session.history.messages()
        if messages:
            try:
                # Limit database save time to prevent blocking shutdown indefinitely
                await asyncio.wait_for(
                    asyncio.to_thread(save_transcript, ctx.room.name, messages),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"Supabase transcript save timed out (5s limit) for session {ctx.room.name}"
                )
            except Exception as e:
                logger.error(
                    f"Error in on_shutdown transcript saving for session {ctx.room.name}: {e}"
                )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            # Fokus pada voice + text
            video_input=False,
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
