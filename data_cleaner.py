import pandas as pd
from dictionaries.dictionary_to_clear import (
    remove_values_from_ternopil,
    remove_values_from_frankivsk
)
from dictionaries.replacment_city_dictionaries import (
    replace_ternopil_city_dict,
    replace_frankivsk_city_dict
)
from dictionaries.replacement_street_dictionaries import (
    replace_ternopil_street_dict,
    replace_frankivsk_street_dict
)
from dictionaries.mr_dictionary import (
    territory_ternopil_mr,
    street_ternopil_territory,
    territory_frankivsk_mr,
    street_frankivsk_territory
)
from dictionaries.product_dictionaryes import products_dict


# Функція видалення лишніх знаків та пробілів
def clean_text(series):
    return series.astype(str).apply(lambda x: x.replace('\n', '').replace('\t', '').strip())


def change_district_name(region: str):
    region = str(region).strip()
    if region == "10. Івано-Франк":
        return "Івано-Франківська"
    elif region == "24. Тернопіль":
        return "Тернопільська"
    elif region == "21. Ужгород":
        return "Ужгородська"

    return region


# Функція для видалення значень
def remove_unwanted(text, region_values):
    if isinstance(text, str):  # Перевіряємо, чи це рядок
        for val in region_values:
            text = text.replace(val, "")  # Поетапна заміна
    return text.strip()  # Видалення зайвих пробілів


def replacement_city(text, city_values):
    if isinstance(text, str):  # Переконуємось, що значення - це рядок
        for key, value in city_values.items():  # Використовуємо city_values, якщо це словник
            text = text.replace(key, value)  # Поетапна заміна
    return text.strip()  # Видаляємо зайві пробіли


def replacement_street(text, street_values):
    if isinstance(text, str):  # Переконуємось, що значення рядок
        for key, value in street_values.items():
            text = text.replace(key, value)  # Замінюємо ключ на значення
        return text.strip()  # Видаляємо зайві пробіли


# Витягуємо назву міста
def extract_city(address):
    # Витягуємо текст до першої коми
    part_before_comma = address.split(',')[0].strip()
    # Повертаємо текст до коми
    return part_before_comma


# Функція для отримання назв вулиць
def extract_street(address_street):
    parts = address_street.split(',')
    return parts[1].strip() if len(parts) > 1 else ""  # Перевіряємо, чи є хоча б 2 частини


# Функція для отримання номуру будинку
def extract_num_house(address_street):
    parts = address_street.split(',')
    return parts[2].strip() if len(parts) > 2 else ""  # Перевіряємо, чи є хоча б 3 частини


# Функція яка визначає приналежність до певної території відповідно до міста
def mr_district(text, dict):
    if isinstance(text, str):  # Перевіряємо, чи це рядок
        return dict.get(text, "").strip()
    return text


# Функція яка визначає приналежність до певної території відповідно до вулиці в місті
def update_territory_for_city_streets(df, city_name, street_dict, city):
    def update_row(row):
        if row["region"] == city_name and row["city"] == city:
            for street_key, territory in street_dict.items():
                if pd.notna(row["street"]) and street_key in row["street"]:
                    return territory
        return row["territory"]

    df["territory"] = df.apply(update_row, axis=1)
    return df


# Функція яка визначає приналежність до певної лінії перпарату
def assign_line_from_product_name(name):
    if isinstance(name, str):
        for key in products_dict:
            if key in name:
                return products_dict[key]
    return None


# Функцію очищення колонки адреси, та отримання нових колонок міста, вулиці та номеру бодинку
def clean_delivery_address(df, column, region_name, region_values, city_values, street_values, street_mr, territory,
                           city):
    df[column] = (
        df[column]
        .apply(lambda x: remove_unwanted(x, region_values=region_values))
        .apply(lambda x: replacement_city(x, city_values=city_values))
        .apply(lambda x: replacement_street(x, street_values=street_values))
        .str.replace(",,", ",", regex=True)
    )

    df["city"] = df[column].apply(extract_city).str.strip()
    df["street"] = df[column].apply(extract_street).str.strip()
    df["house_number"] = df[column].apply(extract_num_house).str.strip()
    # Додаємо категоризацію по території, для подальшого зручнішого групування
    df["territory"] = df["city"].apply(lambda x: mr_district(x, territory))
    df = update_territory_for_city_streets(df, region_name, street_mr, city)
    df["product_line"] = df["product_name"].apply(assign_line_from_product_name)
    return df.reset_index(drop=True)


def process_filtered_df(df, cities_by_region):
    """
    Динамічна обробка DataFrame з кількома регіонами.
    """
    # Визначення конфігурацій для регіонів
    region_configs = {
        "24. Тернопіль": {
            "region_values": remove_values_from_ternopil,
            "city_values": replace_ternopil_city_dict,
            "street_values": replace_ternopil_street_dict,
            "street_mr": street_ternopil_territory,
            "territory": territory_ternopil_mr,
        },
        "10. Івано-Франк": {
            "region_values": remove_values_from_frankivsk,
            "city_values": replace_frankivsk_city_dict,
            "street_values": replace_frankivsk_street_dict,
            "street_mr": street_frankivsk_territory,
            "territory": territory_frankivsk_mr,
        },
        "21. Ужгород": {
            "region_values": [],
            "city_values": {},
            "street_values": {},
            "street_mr": {},
            "territory": {},
        },
    }

    def process_row(row):
        region_name = row.get("region", "")
        col = "delivery_address"
        config = region_configs.get(region_name)
        if not config:
            return row  # Пропускаємо, якщо регіон не розпізнано

        # Очищення адреси
        cleaned_address = remove_unwanted(row[col], config["region_values"])
        cleaned_address = replacement_city(cleaned_address, config["city_values"])
        cleaned_address = replacement_street(cleaned_address, config["street_values"])
        cleaned_address = cleaned_address.replace(",,", ",")

        row["delivery_address"] = cleaned_address
        filename = df.attrs.get("source_filename", "")
        if filename:
            last_15 = filename[-15:]
            result = last_15[:-5]  # відрізаємо останні 4 символи
            try:
                row["source_file_date"] = pd.to_datetime(result, format="%Y_%m_%d").strftime("%Y-%m-%d")
            except Exception:
                row["source_file_date"] = ""
        else:
            row["source_file_date"] = ""

        row["city"] = extract_city(cleaned_address).strip().replace(" ", "")
        row["street"] = extract_street(cleaned_address).strip()
        row["house_number"] = extract_num_house(cleaned_address).strip()
        row["territory"] = mr_district(row["city"], config["territory"])

        expected_city = cities_by_region.get(region_name)
        if expected_city and row["city"] == expected_city:
            for street_key, territory_value in config["street_mr"].items():
                if pd.notna(row["street"]) and street_key in row["street"]:
                    row["territory"] = territory_value
                    break

        row["product_line"] = assign_line_from_product_name(row.get("product_name", ""))
        return row

    df = df.apply(process_row, axis=1)
    return df.reset_index(drop=True)
