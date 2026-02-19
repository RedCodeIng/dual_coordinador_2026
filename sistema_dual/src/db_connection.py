import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Returns a cached Supabase client instance.
    """
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        st.error("Supabase credentials not found in environment variables.")
        st.stop()

    return create_client(url, key)
