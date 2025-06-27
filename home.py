import streamlit as st
from streamlit_option_menu import option_menu
from script import main

from rep_data.sales_data_rep import show_data_rep
from region.district import show_data_sales
from upload_csv import upload_excel




with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["Дашборд продаж","Територія", "Динаміка МП","Завантаження даних"],
        icons=["house","back" ,"bar-chart","upload"],
        menu_icon="cast",
        default_index=0,
        #orientation="horizontal",
        key="main_menu"
    )

if selected == "Дашборд продаж":
    main()

if selected == "Територія":
    show_data_sales()

if selected == "Динаміка МП":
    show_data_rep()

if selected == "Завантаження даних":
    upload_excel()
