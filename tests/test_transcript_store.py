from unittest.mock import MagicMock, patch

from livekit.agents.llm import ChatMessage

from transcript_store import save_transcript


def test_save_transcript_formats_and_inserts():
    # Arrange
    messages = [
        ChatMessage(role="user", content=["Hello Aiko!"]),
        ChatMessage(
            role="assistant",
            content=["Hi there! How can I help you improve your English today?"],
        ),
        ChatMessage(role="user", content=["I want to practice conversation."]),
        # System messages should be ignored in formatting
        ChatMessage(role="system", content=["system instruction"]),
    ]

    session_id = "test_session_123"

    # Mock supabase client
    mock_supabase_client = MagicMock()
    mock_table = mock_supabase_client.table.return_value
    mock_insert = mock_table.insert.return_value

    with patch("transcript_store.supabase", mock_supabase_client):
        # Act
        save_transcript(session_id, messages)

        # Assert
        mock_supabase_client.table.assert_called_once_with("transcripts")

        expected_transcript = (
            "User:\nHello Aiko!\n\n"
            "AIKO:\nHi there! How can I help you improve your English today?\n\n"
            "User:\nI want to practice conversation."
        )

        mock_table.insert.assert_called_once_with(
            {"session_id": session_id, "transcript": expected_transcript}
        )
        mock_insert.execute.assert_called_once()


def test_save_transcript_empty_messages():
    # Arrange
    messages = []
    session_id = "test_session_empty"

    # Mock supabase client
    mock_supabase_client = MagicMock()

    with patch("transcript_store.supabase", mock_supabase_client):
        # Act
        save_transcript(session_id, messages)

        # Assert
        mock_supabase_client.table.assert_not_called()


def test_save_transcript_supabase_exception_logged():
    # Arrange
    messages = [ChatMessage(role="user", content=["Hello"])]
    session_id = "test_session_error"

    # Mock supabase client to raise exception
    mock_supabase_client = MagicMock()
    mock_supabase_client.table.side_effect = Exception("Supabase connection error")

    with patch("transcript_store.supabase", mock_supabase_client):
        # Act & Assert
        # Should not raise exception
        save_transcript(session_id, messages)
        mock_supabase_client.table.assert_called_once_with("transcripts")
