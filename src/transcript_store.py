import logging

from livekit.agents.llm import ChatMessage

from supabase_client import supabase

logger = logging.getLogger(__name__)


def save_transcript(session_id: str, messages: list[ChatMessage]) -> None:
    """
    Formats the conversation transcript and saves it to Supabase in a single row.
    """
    if supabase is None:
        logger.warning(
            f"Supabase client not initialized. Skipping transcript save for session {session_id}."
        )
        return

    # Format the transcript
    transcript_parts = []
    for msg in messages:
        if msg.role == "user":
            content = msg.text_content or ""
            transcript_parts.append(f"User:\n{content}")
        elif msg.role == "assistant":
            content = msg.text_content or ""
            transcript_parts.append(f"AIKO:\n{content}")

    if not transcript_parts:
        logger.info(
            f"No user or assistant messages found for session {session_id}. Nothing to save."
        )
        return

    full_transcript = "\n\n".join(transcript_parts)

    # Insert into Supabase
    try:
        data = {"session_id": session_id, "transcript": full_transcript}
        logger.info(
            f"Saving transcript for session {session_id} to Supabase transcripts table..."
        )
        response = supabase.table("transcripts").insert(data).execute()
        logger.info(
            f"Successfully saved transcript for session {session_id}: {response}"
        )
    except Exception as e:
        logger.error(
            f"Failed to save transcript for session {session_id} to Supabase: {e}",
            exc_info=True,
        )
