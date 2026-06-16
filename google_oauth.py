import os
import re
from urllib.parse import urlencode

import streamlit as st
from google.oauth2.credentials import Credentials
from google_utils import create_flow, credentials_to_dict, credentials_from_dict, get_authorization_url, exchange_code_for_credentials

GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/")


def get_google_state():
    return st.session_state.get("google_oauth_state")


def authorize_google():
    auth_url, state = get_authorization_url(GOOGLE_REDIRECT_URI)
    st.session_state["google_oauth_state"] = state
    st.markdown(f"[Click here to authorize Google]({auth_url})")
    st.write("After authorization, copy the full redirect URL and paste it below.")
    redirect_response = st.text_input("Redirect URL after consent")
    if redirect_response:
        match = re.search(r"code=([^&]+)", redirect_response)
        if match:
            code = match.group(1)
            credentials = exchange_code_for_credentials(code, GOOGLE_REDIRECT_URI)
            st.session_state["google_credentials"] = credentials_to_dict(credentials)
            st.success("Google authorization complete.")
            return credentials
        else:
            st.error("Unable to parse authorization code from redirect URL.")
    return None


def get_google_credentials() -> Credentials | None:
    creds_info = st.session_state.get("google_credentials")
    if creds_info:
        return credentials_from_dict(creds_info)
    return None
