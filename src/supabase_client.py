import logging
import os

from dotenv import load_dotenv
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(".env.local")

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client | None = None

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client successfully initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}", exc_info=True)
else:
    logger.warning(
        "Supabase environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) "
        "are not set. Supabase integration will be disabled."
    )
