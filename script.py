import streamlit as st
import pandas as pd
import plotly.express as px



def main():
    tab1, tab2, tab3 = st.tabs(["Закарпаття", "Франківськ", "Тернопіль"])

    with tab1:
        # --- Дані ---
        full_months = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
                       "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

        data = {
            "Рік": [],
            "Місяць": [],
            "Обсяг (уп.)": [],
            "Сума (грн)": []
        }

        raw_data = {
            2022: [2118,	616304,	2303,	604831,	1479,	453703,	2100,	560958,	1588,	436293,	1439,
                   400815,	2326,	632512,	1173,	344932,	2384,	746046,	1319,	445338,	2156,	751650,	2528,	922485],
            2023: [2556, 919894, 1877, 734646, 2438, 949108, 2099, 805817, 2062, 837388, 1887, 824256,
                   1644, 672264, 2049, 894975, 2558, 1145809, 1624, 689082, 1706, 753126, 1336, 566975],
            2024: [2364, 1051896, 1852, 817549, 2239, 1026967, 2281, 1051436, 1795, 798985, 2225, 1055998,
                   1974, 927515, 1922, 924807, 1893, 902224, 2566, 1287506, 2325, 1218878, 2093, 1089686],
            2025: [1937, 984370, 2195, 1171898, 2353, 1301441, 1763, 990816, 1956, 1134646]
        }

        for year in [2022,2023, 2024, 2025]:
            values = raw_data.get(year, [])
            for i, month in enumerate(full_months):
                data["Рік"].append(year)
                data["Місяць"].append(month)
                if i * 2 + 1 < len(values):
                    data["Обсяг (уп.)"].append(values[i * 2])
                    data["Сума (грн)"].append(values[i * 2 + 1])
                else:
                    data["Обсяг (уп.)"].append(None)
                    data["Сума (грн)"].append(None)

        df = pd.DataFrame(data)
        df["Місяць"] = pd.Categorical(df["Місяць"], categories=full_months, ordered=True)
        df["Середній чек"] = df["Сума (грн)"] / df["Обсяг (уп.)"]

        # --- Заголовок ---
        st.title("📊 Дашборд продажів по регіону: Закарпаття")

        # --- KPI Cards ---
        # --- KPI Cards ---
        st.subheader("🔢 Підсумкові показники по роках")

        col1, col2, col3, col4 = st.columns(4)

        for year, col in zip([2022, 2023, 2024, 2025], [col1, col2, col3, col4]):
            # Сума в грн
            total_sum = df[df["Рік"] == year]["Сума (грн)"].sum()
            previous_sum = df[df["Рік"] == (year - 1)]["Сума (грн)"].sum()
            delta_sum = f"{(total_sum - previous_sum) / previous_sum:.1%}" if previous_sum else "—"

            # Упаковки
            total_units = df[df["Рік"] == year]["Обсяг (уп.)"].sum()
            previous_units = df[df["Рік"] == (year - 1)]["Обсяг (уп.)"].sum()
            delta_units = f"{(total_units - previous_units) / previous_units:.1%}" if previous_units else "—"

            col.metric(f"Сума за {year} (грн)", f"{total_sum:,.0f}", delta_sum)
            col.metric(f"Упаковки за {year}", f"{total_units:,.0f}", delta_units)

        # --- Графіки ---
        st.subheader("📈 Продажі у гривнях")
        st.plotly_chart(px.line(df, x="Місяць", y="Сума (грн)", color="Рік", markers=True), use_container_width=True)

        st.subheader("📦 Продажі в упаковках")
        st.plotly_chart(px.line(df, x="Місяць", y="Обсяг (уп.)", color="Рік", markers=True), use_container_width=True)

        st.subheader("💰 Середній чек (грн / уп.)")
        st.plotly_chart(px.line(df, x="Місяць", y="Середній чек", color="Рік", markers=True), use_container_width=True)

        # --- Таблиця ---
        st.subheader("📄 Таблиця по вибраному року")
        selected_year = st.selectbox("Оберіть рік:", df["Рік"].unique(), key="zakarpat")
        st.dataframe(df[df["Рік"] == selected_year].reset_index(drop=True), use_container_width=True)
    with tab2:


        # Повні назви місяців
        months = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
                  "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

        # Вихідні дані по роках
        raw_data = {
            2023: [3624, 1300032.63, 3449, 1307180.224, 4256, 1586944.108, 3477, 1277983.45, 3488, 1367056.557,
                   3281, 1271070.101, 3308, 1307494.899, 3210, 1296404.84, 3288, 1273796.381, 3426, 1337554.69,
                   3869, 1582592.567, 3363, 1363627.171],
            2024: [3966, 1685581.66, 3968, 1703964.872, 3875, 1722723.289, 3491, 1535684.104, 3293, 1518496.493,
                   2889, 1344563.181, 3270, 1548738.938, 3436, 1598489.619, 3764, 1780718.066, 4270, 2132420.31,
                   3821, 1992584.473, 4317, 2265478.894],
            2025: [4408, 2384938.5, 4126, 2224246.714, 3923, 2114451.55, 3601, 2015096.51, 3585, 2051865.17]
        }

        # Формування довгого DataFrame
        data = {
            "Рік": [],
            "Місяць": [],
            "Обсяг (уп.)": [],
            "Сума (грн)": []
        }

        for year in [2023, 2024, 2025]:
            values = raw_data.get(year, [])
            for i, month in enumerate(full_months):
                data["Рік"].append(year)
                data["Місяць"].append(month)
                if i * 2 + 1 < len(values):
                    data["Обсяг (уп.)"].append(values[i * 2])
                    data["Сума (грн)"].append(values[i * 2 + 1])
                else:
                    data["Обсяг (уп.)"].append(None)
                    data["Сума (грн)"].append(None)

        df = pd.DataFrame(data)
        df["Місяць"] = pd.Categorical(df["Місяць"], categories=full_months, ordered=True)
        df["Середній чек"] = df["Сума (грн)"] / df["Обсяг (уп.)"]

        # --- Заголовок ---
        st.title("📊 Дашборд продажів по регіону: Франківськ")

        # --- KPI Cards ---
        st.subheader("🔢 Підсумкові показники по роках")

        col1, col2, col3 = st.columns(3)

        for year, col in zip([2023, 2024, 2025], [col1, col2, col3]):
            # Сума в грн
            total_sum = df[df["Рік"] == year]["Сума (грн)"].sum()
            previous_sum = df[df["Рік"] == (year - 1)]["Сума (грн)"].sum()
            delta_sum = f"{(total_sum - previous_sum) / previous_sum:.1%}" if previous_sum else "—"

            # Упаковки
            total_units = df[df["Рік"] == year]["Обсяг (уп.)"].sum()
            previous_units = df[df["Рік"] == (year - 1)]["Обсяг (уп.)"].sum()
            delta_units = f"{(total_units - previous_units) / previous_units:.1%}" if previous_units else "—"

            col.metric(f"Сума за {year} (грн)", f"{total_sum:,.0f}", delta_sum)
            col.metric(f"Упаковки за {year}", f"{total_units:,.0f}", delta_units)

        # --- Графіки ---
        st.subheader("📈 Продажі у гривнях")
        st.plotly_chart(px.line(df, x="Місяць", y="Сума (грн)", color="Рік", markers=True), use_container_width=True)

        st.subheader("📦 Продажі в упаковках")
        st.plotly_chart(px.line(df, x="Місяць", y="Обсяг (уп.)", color="Рік", markers=True), use_container_width=True)

        st.subheader("💰 Середній чек (грн / уп.)")
        st.plotly_chart(px.line(df, x="Місяць", y="Середній чек", color="Рік", markers=True), use_container_width=True)

        # --- Таблиця ---
        st.subheader("📄 Таблиця по вибраному року")
        selected_year = st.selectbox("Оберіть рік:", df["Рік"].unique(), key="frankivsk")
        st.dataframe(df[df["Рік"] == selected_year].reset_index(drop=True), use_container_width=True)
    with tab3:
        # Повні назви місяців
        months = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
                  "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

        # Вихідні дані по роках, взяті з зображення
        raw_data = {
            2023: [3539, 1316497.55, 3614, 1371111.896, 4436, 1707149.59, 3246, 1261372.455,
                   3435, 1354105.06, 3607, 1392839.697, 2925, 1231417.106, 3493, 1453472.409,
                   3230, 1379399.683, 3153, 1335257.752, 3441, 1534969.727, 3130, 1371110.051],
            2024: [3652, 1708644.422, 3758, 1677959.069, 3934, 1806192.562, 3186, 1496881.81,
                   2955, 1359941.071, 2831, 1287966.514, 2898, 1434855.861, 3417, 1666852.782,
                   3801, 1983997.049, 3518, 1831820.611, 3313, 1742052.81, 3497, 1860517.708],
            2025: [3803, 2182147.938, 3641, 1932081.49, 3684, 2032575.69, 3179, 1867185.124,
                   3323, 1894080.453]
        }

        # Формування довгого DataFrame
        data = {
            "Рік": [],
            "Місяць": [],
            "Обсяг (уп.)": [],
            "Сума (грн)": []
        }

        for year in [2023, 2024, 2025]:
            values = raw_data.get(year, [])
            for i, month in enumerate(full_months):
                data["Рік"].append(year)
                data["Місяць"].append(month)
                if i * 2 + 1 < len(values):
                    data["Обсяг (уп.)"].append(values[i * 2])
                    data["Сума (грн)"].append(values[i * 2 + 1])
                else:
                    data["Обсяг (уп.)"].append(None)
                    data["Сума (грн)"].append(None)

        df = pd.DataFrame(data)
        df["Місяць"] = pd.Categorical(df["Місяць"], categories=full_months, ordered=True)
        df["Середній чек"] = df["Сума (грн)"] / df["Обсяг (уп.)"]

        # --- Заголовок ---
        st.title("📊 Дашборд продажів по регіону: Тернопіль")

        # --- KPI Cards ---
        st.subheader("🔢 Підсумкові показники по роках")

        col1, col2, col3 = st.columns(3)

        for year, col in zip([2023, 2024, 2025], [col1, col2, col3]):
            # Сума в грн
            total_sum = df[df["Рік"] == year]["Сума (грн)"].sum()
            previous_sum = df[df["Рік"] == (year - 1)]["Сума (грн)"].sum()
            delta_sum = f"{(total_sum - previous_sum) / previous_sum:.1%}" if previous_sum else "—"

            # Упаковки
            total_units = df[df["Рік"] == year]["Обсяг (уп.)"].sum()
            previous_units = df[df["Рік"] == (year - 1)]["Обсяг (уп.)"].sum()
            delta_units = f"{(total_units - previous_units) / previous_units:.1%}" if previous_units else "—"

            col.metric(f"Сума за {year} (грн)", f"{total_sum:,.0f}", delta_sum)
            col.metric(f"Упаковки за {year}", f"{total_units:,.0f}", delta_units)

        # --- Графіки ---
        st.subheader("📈 Продажі у гривнях")
        st.plotly_chart(px.line(df, x="Місяць", y="Сума (грн)", color="Рік", markers=True), use_container_width=True)

        st.subheader("📦 Продажі в упаковках")
        st.plotly_chart(px.line(df, x="Місяць", y="Обсяг (уп.)", color="Рік", markers=True), use_container_width=True)

        st.subheader("💰 Середній чек (грн / уп.)")
        st.plotly_chart(px.line(df, x="Місяць", y="Середній чек", color="Рік", markers=True), use_container_width=True)

        # --- Таблиця ---
        st.subheader("📄 Таблиця по вибраному року")
        selected_year = st.selectbox("Оберіть рік:", df["Рік"].unique(), key="ternopil")
        st.dataframe(df[df["Рік"] == selected_year].reset_index(drop=True), use_container_width=True)