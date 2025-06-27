import streamlit as st
import pandas as pd
import re
from region.load_data import df_make

import plotly.express as px

def show_data_sales():
    regions = ["24. Тернопіль", "10. Івано-Франк", "21. Ужгород"]

    tabs = st.tabs(regions)

    for region, tab in zip(regions, tabs):
        with tab:
            df_sales = df_make(region)
            if not df_sales.empty:
                st.dataframe(df_sales)
                grouped_df = df_sales.groupby("product_name")["quantity"].sum().reset_index()

                col1,col2 = st.columns(2)

                with col1:
                    st.dataframe(grouped_df, height=700)


                with col2:

                    grouped_df = grouped_df.sort_values(by='quantity', ascending=True)

                    fig = px.bar(
                        grouped_df,
                        y='product_name',
                        x='quantity',
                        hover_data=['product_name', 'quantity'],
                        labels={'quantity': 'Кількість', 'product_name': 'Назва препарату'},
                        height=700,
                        orientation='h'
                    )
                    fig.add_shape(
                        type='line',
                        x0=50, x1=50,
                        y0=-0.5, y1=len(grouped_df) - 0.5,
                        line=dict(color='red', width=1, dash='solid')
                    )
                    fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')

                    st.plotly_chart(fig, use_container_width=True)

                treemap_fig = px.treemap(
                    grouped_df,
                    path=['product_name'],
                    values='quantity',
                    color='quantity',
                    color_continuous_scale='RdBu',
                    labels={'product_name': 'Назва препарату', 'quantity': 'Кількість'}
                )
                treemap_fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(t=10, l=10, r=10, b=10)
                )
                st.plotly_chart(treemap_fig, use_container_width=True)

                grouped_df_line = df_sales.groupby(["product_line","product_name"])["quantity"].sum().reset_index()
                # Створення Treemap
                treemap_fig = px.treemap(
                    grouped_df_line,
                    path=['product_line', 'product_name'],  # Використовуємо і лінію, і назву препарату
                    values='quantity',
                    color='quantity',
                    color_continuous_scale='RdBu',
                    labels={'product_line': 'Лінія продукту', 'product_name': 'Назва препарату',
                            'quantity': 'Кількість'}
                )

                # Оновлення макету для кращого вигляду
                treemap_fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(t=30, l=10, r=10, b=10),  # Збільшено верхній відступ для заголовка
                    title_text="Розподіл кількості препаратів за лініями",  # Додаємо заголовок до графіка
                    title_x=0.2  # Вирівнюємо заголовок по центру
                )

                # Відображення Treemap у Streamlit
                st.plotly_chart(treemap_fig, use_container_width=True)

                st.write("---")

                df_sales['source_file_date'] = pd.to_datetime(df_sales['source_file_date'])

                # --- ОСНОВНА ЛОГІКА ДОДАТКУ ---

                # Отримання унікальних територій для створення вкладок першого рівня
                unique_territories = df_sales['territory'].unique().tolist()
                unique_territories.sort()

                # Створення вкладок першого рівня (за Територією)
                territory_tabs = st.tabs(unique_territories)

                # Ітерація по кожній вкладці Території
                for i_terr, territory in enumerate(unique_territories):
                    with territory_tabs[i_terr]:
                        st.header(f"Територія: {territory}")

                        # Фільтрація даних для поточної території
                        territory_df = df_sales[df_sales['territory'] == territory].copy()

                        # Отримання унікальних міст для створення вкладок другого рівня в межах цієї території
                        unique_cities_in_territory = territory_df['city'].unique().tolist()
                        unique_cities_in_territory.sort()

                        if not unique_cities_in_territory:
                            st.info(f"Для території '{territory}' немає даних по містах.")
                            continue

                        # Створення вкладок другого рівня (за Містом)
                        city_tabs = st.tabs(unique_cities_in_territory)

                        # Ітерація по кожній вкладці Міста
                        for i_city, city in enumerate(unique_cities_in_territory):
                            with city_tabs[i_city]:
                                st.subheader(f"Місто: {city}")

                                # Фільтрація даних для поточного міста та території
                                city_territory_df = territory_df[territory_df['city'] == city].copy()

                                # --- ФІЛЬТР ЗА ВУЛИЦЕЮ ---
                                # Перетворюємо назви вулиць на Title Case для кращого відображення (наприклад, "вул.Зарічна" -> "Вул.Зарічна")
                                # Також очищаємо від зайвих пробілів і приводимо до одного регістру для унікальності
                                city_territory_df['street_normalized'] = city_territory_df[
                                    'street'].str.strip().str.title()
                                unique_streets = ['Усі вулиці'] + sorted(
                                    city_territory_df['street_normalized'].unique().tolist())

                                selected_street_display = st.selectbox(
                                    f"Оберіть вулицю для {city}",
                                    unique_streets,
                                    key=f"{territory}_{city}_street_filter"
                                )

                                # Фільтрація даних за обраною вулицею (використовуємо оригінальну колонку street для фільтрації,
                                # щоб уникнути проблем з регістрами, якщо оригінальні дані неоднорідні)
                                if selected_street_display != 'Усі вулиці':
                                    # Знову знаходимо оригінальне написання вулиці
                                    # Це потрібно, якщо в унікальних назвах були різні регістри, але в основній колонці вони послідовні
                                    # Використовуємо .isin() для гнучкості, якщо кілька оригінальних написань відповідають нормалізованому
                                    original_streets_matching_normalized = city_territory_df[
                                        city_territory_df['street_normalized'] == selected_street_display][
                                        'street'].unique().tolist()
                                    filtered_df_for_display = city_territory_df[
                                        city_territory_df['street'].isin(original_streets_matching_normalized)]
                                else:
                                    filtered_df_for_display = city_territory_df

                                # Отримання унікальних комбінацій клієнтів та адрес для відображення
                                unique_clients_addresses = filtered_df_for_display[
                                    ['client', 'delivery_address']].drop_duplicates()

                                if not unique_clients_addresses.empty:
                                    for index, row in unique_clients_addresses.iterrows():
                                        client_name = row['client']
                                        delivery_address = row['delivery_address']

                                        # Використання st.expander для згортання/розгортання
                                        expander_title = f"**Клієнт:** {client_name}  |  **Адреса:** {delivery_address}"
                                        with st.expander(expander_title):
                                            # Фільтрація даних для поточного клієнта та адреси
                                            client_address_df = filtered_df_for_display[
                                                (filtered_df_for_display['client'] == client_name) &
                                                (filtered_df_for_display['delivery_address'] == delivery_address)
                                                ]

                                            # Отримання унікальних product_line для даного клієнта/адреси
                                            unique_product_lines = client_address_df['product_line'].unique().tolist()
                                            unique_product_lines.sort()

                                            if not client_address_df.empty:
                                                for product_line in unique_product_lines:
                                                    st.markdown(f"##### Лінія продукту: {product_line}")

                                                    # Фільтрація даних для поточної лінії продукту
                                                    product_line_df = client_address_df[
                                                        client_address_df['product_line'] == product_line
                                                        ]

                                                    # Створення зведеної таблиці для поточної лінії продукту
                                                    if not product_line_df.empty:
                                                        pivot_table = pd.pivot_table(
                                                            product_line_df,
                                                            values='quantity',
                                                            index='source_file_date',
                                                            columns='product_name',
                                                            aggfunc='sum',
                                                            fill_value=0
                                                        )
                                                        st.dataframe(pivot_table, use_container_width=True)
                                                        st.write("---")
                                                    else:
                                                        st.info(f"Немає даних для лінії '{product_line}'.")
                                            else:
                                                st.info("Немає даних про кількість для цієї комбінації клієнта та адреси.")
                                else:
                                    st.info("Немає клієнтів для цього міста.")
            else:
                st.warning(f"Немає даних для {region}")