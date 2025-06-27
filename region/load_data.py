import streamlit as st
import pandas as pd
from supabase import create_client, Client

def fetch_data(supabase, region):
    all_data = []
    limit = 1000
    offset = 0

    while True:
        response = supabase.table("sales_data_month")\
            .select("*")\
            .eq("region", region)\
            .limit(limit)\
            .offset(offset)\
            .execute()

        if hasattr(response, "error") and response.error:
            st.error(f"Помилка при отриманні даних: {response.error.message}")
            break

        batch = response.data
        if not batch:
            break

        all_data.extend(batch)
        offset += limit

    return pd.DataFrame(all_data)

def df_make(region):

    url = "https://vimswywxzejgyvxjzuvf.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpbXN3eXd4emVqZ3l2eGp6dXZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NTk5NDYsImV4cCI6MjA2MTQzNTk0Nn0.bqcMzJaUet9yPsUEuXe6cqvKjzOBOBvQzBG6eXFl0VU"
    supabase: Client = create_client(url, key)



    df_sales = fetch_data(supabase, region)
    return df_sales
