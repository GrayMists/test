import streamlit as st
import pandas as pd
import requests
import json
from data_cleaner import process_filtered_df

# Вкажи свої дані Supabase
url = "https://vimswywxzejgyvxjzuvf.supabase.co/rest/v1/sales_data_month"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpbXN3eXd4emVqZ3l2eGp6dXZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NTk5NDYsImV4cCI6MjA2MTQzNTk0Nn0.bqcMzJaUet9yPsUEuXe6cqvKjzOBOBvQzBG6eXFl0VU"

def rename_columns(df):
    rename_dict = {
        "Дистриб'ютор": "distributor",
        "Регіон": "region",
        "Місто": "city",
        "Клієнт": "client",
        "Факт.адреса доставки": "delivery_address",
        "Найменування": "product_name",
        "Кількість": "quantity",
    }
    df = df.rename(columns=rename_dict)
    return df

def upload_excel():
    st.title("Завантаження Excel")
    uploaded_file = st.file_uploader("Завантаж Excel файл", type=["xls", "xlsx"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            df.attrs["source_filename"] = uploaded_file.name
            df = df.dropna(how='all')
            df = df.fillna("")
            required_columns = ["Регіон", "Місто", "Клієнт", "Факт.адреса доставки", "Найменування", "Кількість", "Дистриб'ютор"]
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                st.error(f"У файлі відсутні колонки: {', '.join(missing)}")
                return
            df = df[df["Регіон"].isin(["24. Тернопіль"])].reset_index(drop=True)
            df = df.drop(columns=["ЄДРПОУ", "Юр. адреса клієнта", "Adding"], errors='ignore')

            df = rename_columns(df)
            cities_by_region = {
                "24. Тернопіль": "м.Тернопіль",
                "10. Івано-Франк": "м.Івано-Франківськ",
                "21. Ужгород": "м.Ужгород"
            }

            st.write("Ось ваш датафрейм з перейменованими колонками:")
            df = process_filtered_df(df, cities_by_region)
            st.dataframe(df)


            if st.button("Завантажити в Supabase"):
                headers = {
                    "apikey": key,
                    "Authorization": key,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }
                data = df.to_dict(orient="records")
                chunk_size = 500
                success = True

                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i+chunk_size]
                    response = requests.post(url, headers=headers, data=json.dumps(chunk))
                    if response.status_code not in [200, 201]:
                        st.error(f"Помилка при завантаженні: {response.text}")
                        success = False
                        break

                if success:
                    st.success("Дані успішно завантажені в Supabase!")

            return df

        except Exception as e:
            st.error(f"Помилка при обробці: {e}")

upload_excel()