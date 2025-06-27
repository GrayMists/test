import requests
import pandas as pd
import streamlit as st

SUPABASE_URL = "https://vimswywxzejgyvxjzuvf.supabase.co"
SUPABASE_KEY = "9sZSIsImlhdCI6MTc0NTg1OTk0NiwiZXhwIjoyMDYxNDM1OTQ2fQ.31GnQn8Bf_tcM-JXIdP4fk8Hnf3wMEKrhofd4Vy3EiY"
TABLE_NAME = "sales_data_rep"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

@st.cache_data
def fetch_sales_data():
    all_data = []
    limit = 1000
    offset = 0

    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
            headers=headers,
            params={
                "select": "*",
                "limit": limit,
                "offset": offset
            }
        )
        if response.status_code != 200:
            raise Exception(f"Помилка при отриманні даних: {response.text}")

        data = response.json()
        if not data:
            break
        all_data.extend(data)
        offset += limit

    df_rep = pd.DataFrame(all_data)
    return df_rep