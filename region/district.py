import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from region.load_data import df_make


# --- 1. КЕШУВАННЯ ТА ЗАВАНТАЖЕННЯ ДАНИХ ---
@st.cache_data
def load_and_prepare_data(region):
    """
    Завантажує та попередньо обробляє дані для вказаного регіону.
    """
    df = df_make(region)
    if not df.empty:
        df['source_file_date'] = pd.to_datetime(df['source_file_date'])
        df['street_normalized'] = df['street'].str.strip().str.title()
    return df


# --- 2. ФУНКЦІЇ АНАЛІЗУ ТА ВІЗУАЛІЗАЦІЇ ---
def analyze_sales_dynamics(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Аналізує динаміку продажів, групуючи дані.
    Повертає "плаский" DataFrame з колонками замість рівнів індексу.
    """
    df = raw_df.copy()
    df['month'] = df['source_file_date'].dt.strftime('%Y-%m')
    df['period_code'] = df['source_file_date'].dt.day

    pivot_df = df.pivot_table(
        index=['month', 'territory', 'product_line', 'product_name'],
        columns='period_code',
        values='quantity',
        aggfunc='sum'
    ).fillna(0)

    clean_sales_df = pd.DataFrame(index=pivot_df.index)

    sales_d10 = pivot_df.get(10, 0)
    sales_d20 = pivot_df.get(20, 0)

    clean_sales_df['Декада 1'] = sales_d10
    clean_sales_df['Декада 2'] = sales_d20 - sales_d10
    clean_sales_df['Декада 3'] = pivot_df.get(30, 0) - sales_d20

    clean_sales_df['Місяць Всього'] = clean_sales_df[['Декада 1', 'Декада 2', 'Декада 3']].sum(axis=1)

    return clean_sales_df.reset_index()


def calculate_and_format_decades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Бере DataFrame, розраховує "чисті" продажі по декадах та форматує
    у зведену таблицю з датами в рядках та препаратами в колонках.
    Коректно обробляє місяці з неповними даними.
    """
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df['month'] = df['source_file_date'].dt.strftime('%Y-%m')
    df['period_code'] = df['source_file_date'].dt.day

    pivot_df = df.pivot_table(
        index=['month', 'product_name'], columns='period_code',
        values='quantity', aggfunc='sum'
    )

    all_data = []

    for month, month_df in pivot_df.groupby(level='month'):
        has_d10 = 10 in month_df.columns
        has_d20 = 20 in month_df.columns
        has_d30 = 30 in month_df.columns

        sales_d10 = month_df.get(10, pd.Series(0, index=month_df.index)).fillna(0)
        sales_d20 = month_df.get(20, pd.Series(0, index=month_df.index)).fillna(0)
        sales_d30 = month_df.get(30, pd.Series(0, index=month_df.index)).fillna(0)

        # Спеціальний випадок: є тільки загальна сума за місяць
        if has_d30 and not has_d20 and not has_d10:
            for (m, product), quantity in sales_d30.items():
                if quantity > 0:
                    all_data.append(
                        {'Період': f"{month} - Місяць Всього", 'product_name': product, 'quantity': quantity})
        else:  # Стандартний розрахунок
            d1 = sales_d10
            d2 = sales_d20 - sales_d10
            d3 = sales_d30 - sales_d20

            for (m, product), q1 in d1.items():
                if q1 > 0: all_data.append({'Період': f"{month} - Декада 1", 'product_name': product, 'quantity': q1})
            for (m, product), q2 in d2.items():
                if q2 > 0: all_data.append({'Період': f"{month} - Декада 2", 'product_name': product, 'quantity': q2})
            for (m, product), q3 in d3.items():
                if q3 > 0: all_data.append({'Період': f"{month} - Декада 3", 'product_name': product, 'quantity': q3})

    if not all_data:
        return pd.DataFrame()

    long_format_df = pd.DataFrame(all_data)
    final_pivot = long_format_df.pivot_table(
        index='Період', columns='product_name', values='quantity', aggfunc='sum'
    ).fillna(0)

    return final_pivot.sort_index()


def create_waterfall_chart(df, base_month, comp_month):
    """Створює водоспадну діаграму для аналізу вкладу."""
    base_col = f'Підсумок ({base_month})'
    comp_col = f'Підсумок ({comp_month})'
    base_month_total = df[base_col].sum()
    comp_month_total = df[comp_col].sum()

    fig = go.Figure(go.Waterfall(
        name="Динаміка", orientation="v",
        measure=["relative"] * len(df) + ["total", "total"],
        x=df.index.tolist() + [f'Всього {base_month}', f'Всього {comp_month}'],
        text=[f"{v:+.1f}" for v in df['Динаміка']] + [f"{base_month_total:.1f}", f"{comp_month_total:.1f}"],
        textposition="outside",
        y=df['Динаміка'].tolist() + [base_month_total, comp_month_total],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    fig.update_layout(title_text="Аналіз вкладу: Які препарати вплинули на результат?", showlegend=False)
    return fig


def create_growth_scatter_plot(df, base_month, comp_month):
    """Створює матрицю зростання (точкову діаграму)."""
    base_col = f'Підсумок ({base_month})'
    comp_col = f'Підсумок ({comp_month})'

    fig = px.scatter(
        df, x=base_col, y=comp_col,
        text=df.index,
        title="Матриця зростання: Хто впав, а хто виріс?",
        labels={base_col: f"Продажі {base_month}", comp_col: f"Продажі {comp_month}"}
    )
    max_val = max(df[base_col].max(), df[comp_col].max()) * 1.1
    fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="Red", dash="dash"))
    fig.update_traces(textposition='top center')
    return fig


def display_summary_charts(df):
    """Створює та відображає зведені графіки (Bar, Treemaps)."""
    st.header("Загальний аналіз продажів")
    grouped_by_product = df.groupby("product_name")["quantity"].sum().reset_index()
    if grouped_by_product.empty:
        st.warning("Немає даних для побудови зведених графіків.")
        return

    col1, col2 = st.columns([2, 3])
    with col1:
        st.write("Сумарна кількість за препаратом:")
        st.dataframe(grouped_by_product.sort_values(by='quantity', ascending=False), height=700, hide_index=True)
    with col2:
        bar_fig = px.bar(
            grouped_by_product.sort_values(by='quantity', ascending=True),
            y='product_name', x='quantity',
            labels={'quantity': 'Кількість', 'product_name': 'Назва препарату'},
            height=800, orientation='h', title="Рейтинг препаратів за кількістю"
        )
        mean_quantity = grouped_by_product['quantity'].mean()
        bar_fig.add_shape(type='line', x0=mean_quantity, x1=mean_quantity, y0=-0.5, y1=len(grouped_by_product) - 0.5,
                          line=dict(color='red', width=2, dash='dash'))
        bar_fig.add_annotation(x=mean_quantity, y=len(grouped_by_product) * 0.95, text="Середнє", showarrow=False,
                               xanchor="left")
        st.plotly_chart(bar_fig, use_container_width=True)

    st.header("Структура продажів")
    grouped_by_line = df.groupby(["product_line", "product_name"])["quantity"].sum().reset_index()
    if not grouped_by_line.empty:
        treemap_fig_line = px.treemap(
            grouped_by_line, path=['product_line', 'product_name'], values='quantity', color='quantity',
            color_continuous_scale='Viridis', title="Розподіл кількості за лініями продуктів та препаратами"
        )
        st.plotly_chart(treemap_fig_line, use_container_width=True)


def display_mp_sales(df_for_decades, df_for_period_filter):
    """
    Відображає дані про продажі з вкладками для кожної товарної лінії.
    """
    st.header("Продажі за товарними лініями")

    with st.expander("Інформація по декадах"):
        if df_for_decades.empty:
            st.info("Немає даних для розрахунку по декадах.")
        else:
            unique_product_lines = sorted(df_for_decades['product_line'].unique().tolist())
            if not unique_product_lines:
                st.info("В обраних даних відсутні товарні лінії.")
            else:
                line_tabs = st.tabs(unique_product_lines)
                for i, line in enumerate(unique_product_lines):
                    with line_tabs[i]:
                        line_df = df_for_decades[df_for_decades['product_line'] == line]
                        st.subheader(f"Деталізація продажів для лінії: {line}")
                        final_pivot = calculate_and_format_decades(line_df)
                        if not final_pivot.empty:
                            st.dataframe(final_pivot.style.format("{:.1f}").background_gradient(cmap='Blues', axis=1))
                        else:
                            st.info(f"Немає продажів для лінії '{line}'.")

    st.subheader("Загальні продажі за обраний у фільтрі період")
    if df_for_period_filter.empty:
        st.info(
            "Немає даних для відображення за обраним фільтром періоду. Оберіть 'Весь період' для перегляду всіх даних.")
    else:
        agg_pivot = pd.pivot_table(
            df_for_period_filter,
            values='quantity',
            index=df_for_period_filter['source_file_date'].dt.date,
            columns='product_name',
            aggfunc='sum'
        ).fillna(0)
        st.dataframe(agg_pivot.style.format("{:.1f}").background_gradient(cmap='Greens', axis=1))


def display_detailed_view(df_for_decades):
    """
    Відображає деталізований перегляд за клієнтами.
    """
    st.header("Деталізований перегляд за клієнтами")
    unique_clients_addresses = df_for_decades[['client', 'delivery_address']].drop_duplicates().sort_values(by='client')
    if unique_clients_addresses.empty:
        st.info("Немає клієнтів, що відповідають фільтрам.")
        return

    for _, row in unique_clients_addresses.iterrows():
        client_name, delivery_address = row['client'], row['delivery_address']
        with st.expander(f"**Клієнт:** {client_name}  |  **Адреса:** {delivery_address}"):
            client_df_decades = df_for_decades[
                (df_for_decades['client'] == client_name) & (df_for_decades['delivery_address'] == delivery_address)]

            st.subheader("Інформація по декадах")
            if client_df_decades.empty:
                st.info("Немає даних для розрахунку по декадах для цього клієнта.")
            else:
                unique_product_lines = sorted(client_df_decades['product_line'].unique().tolist())
                if not unique_product_lines:
                    st.info("У цього клієнта немає даних по товарних лініях.")
                else:
                    line_tabs = st.tabs(unique_product_lines)
                    for i, line in enumerate(unique_product_lines):
                        with line_tabs[i]:
                            line_df = client_df_decades[client_df_decades['product_line'] == line]
                            final_pivot = calculate_and_format_decades(line_df)
                            if not final_pivot.empty:
                                st.dataframe(
                                    final_pivot.style.format("{:.1f}").background_gradient(cmap='Blues', axis=1))
                            else:
                                st.info(f"Немає даних про продажі для лінії '{line}'.")


# --- ГОЛОВНА ФУНКЦІЯ ДОДАТКУ ---
def show_data_sales():
    st.title("Аналіз продажів по регіонах 📈")

    st.sidebar.header("Фільтри ⚙️")
    regions = ["24. Тернопіль", "10. Івано-Франк", "21. Ужгород"]
    selected_region = st.sidebar.selectbox("Оберіть регіон:", regions)

    if not selected_region:
        st.stop()

    df_sales = load_and_prepare_data(selected_region)
    if df_sales.empty:
        st.warning(f"Немає даних для регіону: {selected_region}")
        st.stop()

    df_filtered = df_sales.copy()
    unique_territories = ['Усі території'] + sorted(df_filtered['territory'].unique().tolist())
    selected_territory = st.sidebar.selectbox("Оберіть територію:", unique_territories)
    if selected_territory != 'Усі території':
        df_filtered = df_filtered[df_filtered['territory'] == selected_territory]

    unique_cities = ['Усі міста'] + sorted(df_filtered['city'].unique().tolist())
    selected_city = st.sidebar.selectbox("Оберіть місто:", unique_cities)
    if selected_city != 'Усі міста':
        df_filtered = df_filtered[df_filtered['city'] == selected_city]

    unique_streets = ['Усі вулиці'] + sorted(df_filtered['street_normalized'].unique().tolist())
    selected_street = st.sidebar.selectbox("Оберіть вулицю:", unique_streets)
    if selected_street != 'Усі вулиці':
        df_filtered = df_filtered[df_filtered['street_normalized'] == selected_street]

    # Створюємо DataFrame для першої вкладки і застосовуємо до нього фільтр по даті
    df_for_general_tabs = df_filtered.copy()
    unique_dates = ['Весь період'] + sorted(df_for_general_tabs['source_file_date'].dt.date.unique().tolist(),
                                            reverse=True)
    selected_date_display = st.sidebar.selectbox("Оберіть дату:", unique_dates)
    if selected_date_display != 'Весь період':
        df_for_general_tabs = df_for_general_tabs[
            df_for_general_tabs['source_file_date'].dt.date == selected_date_display]
        date_filter_text = selected_date_display.strftime('%Y-%m-%d')
    else:
        date_filter_text = "Весь період"

    st.header(f"Показники для: {selected_region}")
    st.info(
        f"Застосовані фільтри: Територія: **{selected_territory}**, Місто: **{selected_city}**, Вулиця: **{selected_street}**, Період: **{date_filter_text}**")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Загальна аналітика", "Продажі МП", "📋 Деталі за клієнтами", "📈 Динаміка декад"])

    with tab1:
        display_summary_charts(df_for_general_tabs)
    with tab2:
        display_mp_sales(df_filtered, df_for_general_tabs)
    with tab3:
        display_detailed_view(df_filtered)
    with tab4:
        st.header("Порівняльний аналіз динаміки продажів")
        st.info("Аналіз проводиться у розрізі територій та товарних ліній.")

        analytics_df = analyze_sales_dynamics(df_filtered)
        if analytics_df.empty:
            st.warning("Немає даних для аналізу динаміки.")
            st.stop()

        territories = sorted(analytics_df['territory'].unique())
        territory_tabs = st.tabs(territories)

        for i, territory in enumerate(territories):
            with territory_tabs[i]:
                st.subheader(f"Територія: {territory}")
                territory_df = analytics_df[analytics_df['territory'] == territory]

                months = sorted(territory_df['month'].unique(), reverse=True)
                if len(months) < 2:
                    st.warning("Для порівняння потрібно мати дані хоча б за два місяці на цій території.")
                    continue

                col1, col2 = st.columns(2)
                base_month = col1.selectbox("Базовий місяць:", months, index=1, key=f"base_month_{i}")
                comparison_month = col2.selectbox("Місяць для порівняння:", months, index=0, key=f"comp_month_{i}")

                if base_month == comparison_month:
                    st.error("Будь ласка, оберіть два різні місяці.")
                    continue

                product_lines = sorted(territory_df['product_line'].unique())
                for line in product_lines:
                    with st.expander(f"**Товарна лінія: {line}**", expanded=True):
                        base_data_full = territory_df[
                            (territory_df['month'] == base_month) & (territory_df['product_line'] == line)]
                        comp_data_full = territory_df[
                            (territory_df['month'] == comparison_month) & (territory_df['product_line'] == line)]

                        available_decades = ['Декада 1']
                        if not comp_data_full.empty:
                            temp_decades = []
                            if comp_data_full['Декада 1'].sum() > 0: temp_decades.append('Декада 1')
                            if comp_data_full['Декада 2'].sum() > 0: temp_decades.append('Декада 2')
                            if comp_data_full['Декада 3'].sum() > 0: temp_decades.append('Декада 3')
                            if temp_decades: available_decades = temp_decades

                        base_data = base_data_full.drop(columns=['month', 'territory', 'product_line', 'Місяць Всього'])
                        comp_data = comp_data_full.drop(columns=['month', 'territory', 'product_line', 'Місяць Всього'])

                        comparison_table = pd.merge(base_data, comp_data, on='product_name', how='outer',
                                                    suffixes=(f' ({base_month})', f' ({comparison_month})')).fillna(0)

                        base_cols = [f'{d} ({base_month})' for d in available_decades]
                        comp_cols = [f'{d} ({comparison_month})' for d in available_decades]

                        comparison_table[f'Підсумок ({base_month})'] = comparison_table[base_cols].sum(axis=1)
                        comparison_table[f'Підсумок ({comparison_month})'] = comparison_table[comp_cols].sum(axis=1)
                        comparison_table['Динаміка'] = comparison_table[f'Підсумок ({comparison_month})'] - \
                                                       comparison_table[f'Підсумок ({base_month})']

                        def _calc_pct_change(c, p):
                            if p == 0: return np.inf if c > 0 else 0.0
                            return (c - p) / p * 100

                        comparison_table['Динаміка %'] = comparison_table.apply(
                            lambda row: _calc_pct_change(row[f'Підсумок ({comparison_month})'],
                                                         row[f'Підсумок ({base_month})']), axis=1)
                        comparison_table.set_index('product_name', inplace=True)

                        viz_tab1, viz_tab2, viz_tab3 = st.tabs(
                            ["Детальна таблиця", "Аналіз вкладу (Waterfall)", "Матриця зростання (Scatter)"])

                        with viz_tab1:
                            display_cols_order = [
                                f'Підсумок ({base_month})', f'Підсумок ({comparison_month})', 'Динаміка', 'Динаміка %',
                                f'Декада 1 ({base_month})', f'Декада 1 ({comparison_month})',
                                f'Декада 2 ({base_month})', f'Декада 2 ({comparison_month})',
                                f'Декада 3 ({base_month})', f'Декада 3 ({comparison_month})'
                            ]
                            final_cols = [col for col in display_cols_order if col in comparison_table.columns]
                            st.dataframe(
                                comparison_table[final_cols].sort_values(by='Динаміка').style.format(precision=1,
                                                                                                     thousands=",").format(
                                    '{:+.1f}%', subset=['Динаміка %']).background_gradient(cmap='RdYlGn',
                                                                                           subset=['Динаміка',
                                                                                                   'Динаміка %']))

                        with viz_tab2:
                            df_for_waterfall = comparison_table[comparison_table['Динаміка'] != 0].copy()
                            if not df_for_waterfall.empty:
                                waterfall_fig = create_waterfall_chart(df_for_waterfall, base_month, comparison_month)
                                st.plotly_chart(waterfall_fig, use_container_width=True)
                            else:
                                st.info("Немає змін для відображення на водоспадній діаграмі.")

                        with viz_tab3:
                            if not comparison_table.empty:
                                scatter_fig = create_growth_scatter_plot(comparison_table, base_month, comparison_month)
                                st.plotly_chart(scatter_fig, use_container_width=True)
                            else:
                                st.info("Немає даних для відображення матриці зростання.")
