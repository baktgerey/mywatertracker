import streamlit as st
import json
import os
from datetime import date, datetime
import pandas as pd

# ── Настройки страницы ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Трекер воды и сна",
    page_icon="💧",
    layout="centered"
)

# ── Константы ───────────────────────────────────────────────────────────────
DATA_FILE = "data.json"
WATER_GOAL = 2000   # мл
SLEEP_GOAL = 8      # часов

# ── Загрузка / сохранение данных ─────────────────────────────────────────────
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def today_str() -> str:
    return str(date.today())

def get_today(data: dict) -> dict:
    td = today_str()
    if td not in data:
        data[td] = {"water": 0, "sleep": None, "sleep_note": "", "water_log": []}
    # Совместимость со старыми записями без water_log
    if "water_log" not in data[td]:
        data[td]["water_log"] = []
    return data[td]

# ── Основное приложение ──────────────────────────────────────────────────────
data = load_data()
today = get_today(data)
today_key = today_str()

st.title("💧😴 Трекер воды и сна")
st.caption(f"Сегодня: {date.today().strftime('%d.%m.%Y')}")

# ════════════════════════════════════════════════════════════════════════════
# БЛОК 1 — ВОДА
# ════════════════════════════════════════════════════════════════════════════
st.header("💧 Вода")

water_pct = min(today["water"] / WATER_GOAL, 1.0)
st.progress(water_pct, text=f"{today['water']} мл из {WATER_GOAL} мл")

if today["water"] >= WATER_GOAL:
    st.success("✅ Норма воды выполнена! Отлично!")
else:
    remaining = WATER_GOAL - today["water"]
    st.info(f"Осталось выпить: {remaining} мл")

col1, col2 = st.columns([2, 1])
with col1:
    water_amount = st.number_input(
        "Добавить воду (мл)",
        min_value=0,
        max_value=2000,
        step=50,
        value=200,
        key="water_input"
    )
with col2:
    st.write("")
    st.write("")
    if st.button("➕ Добавить", use_container_width=True):
        if water_amount <= 0:
            st.warning("Введите количество больше 0.")
        else:
            today["water"] += water_amount
            today["water_log"].append({
                "time": datetime.now().strftime("%H:%M"),
                "amount": water_amount
            })
            save_data(data)
            st.rerun()

# Быстрые кнопки
st.write("Быстрое добавление:")
qcols = st.columns(4)
for i, ml in enumerate([100, 200, 300, 500]):
    with qcols[i]:
        if st.button(f"+{ml} мл", use_container_width=True, key=f"quick_{ml}"):
            today["water"] += ml
            today["water_log"].append({
                "time": datetime.now().strftime("%H:%M"),
                "amount": ml
            })
            save_data(data)
            st.rerun()

# Лог воды за сегодня
if today["water_log"]:
    with st.expander("📋 Лог воды за сегодня"):
        for entry in reversed(today["water_log"]):
            st.write(f"🕐 {entry['time']} — {entry['amount']} мл")

if st.button("🔄 Сбросить воду за сегодня"):
    today["water"] = 0
    today["water_log"] = []
    save_data(data)
    st.rerun()

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# БЛОК 2 — СОН
# ════════════════════════════════════════════════════════════════════════════
st.header("😴 Сон")

sleep_val = today["sleep"] if today["sleep"] is not None else 0.0
sleep_hours = st.number_input(
    "Сколько часов спал этой ночью?",
    min_value=0.0,
    max_value=24.0,
    step=0.5,
    value=float(sleep_val),
    key="sleep_input"
)
sleep_note = st.text_input(
    "Заметка (необязательно)",
    value=today.get("sleep_note", ""),
    placeholder="Например: плохо засыпал, проснулся рано...",
    key="sleep_note_input"
)

if st.button("💾 Сохранить сон", use_container_width=True):
    if sleep_hours < 0:
        st.error("Часы сна не могут быть отрицательными.")
    else:
        today["sleep"] = sleep_hours
        today["sleep_note"] = sleep_note
        save_data(data)
        st.success("Сон сохранён!")
        st.rerun()

# Статус сна
if today["sleep"] is not None:
    sleep_pct = min(today["sleep"] / SLEEP_GOAL, 1.0)
    st.progress(sleep_pct, text=f"{today['sleep']} ч из {SLEEP_GOAL} ч")
    if today["sleep"] >= SLEEP_GOAL:
        st.success("✅ Норма сна выполнена!")
    elif today["sleep"] >= 6:
        st.warning(f"⚠️ Немного не хватает. Норма: {SLEEP_GOAL} ч")
    else:
        st.error(f"❌ Слишком мало сна. Норма: {SLEEP_GOAL} ч")

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# БЛОК 3 — СТАТИСТИКА ЗА НЕДЕЛЮ
# ════════════════════════════════════════════════════════════════════════════
st.header("📊 Статистика за последние 7 дней")

save_data(data)  # убеждаемся, что данные сегодня сохранены

sorted_keys = sorted(data.keys())[-7:]
rows = []
for k in sorted_keys:
    d = data[k]
    rows.append({
        "Дата": k,
        "Вода (мл)": d.get("water", 0),
        "Сон (ч)": d.get("sleep") if d.get("sleep") is not None else 0
    })

if rows:
    df = pd.DataFrame(rows).set_index("Дата")

    tab1, tab2 = st.tabs(["💧 Вода", "😴 Сон"])
    with tab1:
        st.bar_chart(df[["Вода (мл)"]])
        st.caption(f"Норма воды: {WATER_GOAL} мл/день")
    with tab2:
        st.bar_chart(df[["Сон (ч)"]])
        st.caption(f"Норма сна: {SLEEP_GOAL} ч/день")

    st.subheader("Таблица")
    df_display = df.copy()
    df_display["Вода ✅"] = df_display["Вода (мл)"].apply(
        lambda x: "✅" if x >= WATER_GOAL else "❌"
    )
    df_display["Сон ✅"] = df_display["Сон (ч)"].apply(
        lambda x: "✅" if x >= SLEEP_GOAL else "❌"
    )
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("Данных пока нет. Начни записывать сегодня!")
