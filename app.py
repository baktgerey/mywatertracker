import streamlit as st
import json
import os
from datetime import date, datetime, timedelta
import pandas as pd

# ── Настройки страницы ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="HealthTrack — Вода и Сон",
    page_icon="💧",
    layout="wide"
)

# ── Кастомный CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Space+Grotesk:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

.app-header { text-align: center; padding: 2rem 0 1rem 0; }
.app-header h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.8rem; font-weight: 700;
    background: linear-gradient(90deg, #00d2ff, #7b2ff7, #ff6b9d);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}
.app-header p { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 0.3rem; }

.metric-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px; padding: 1.5rem; text-align: center;
    backdrop-filter: blur(10px);
}
.metric-card .icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.metric-card .value { font-size: 2rem; font-weight: 900; color: #fff; line-height: 1; }
.metric-card .label { font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 1px; }
.metric-card .sub { font-size: 0.85rem; color: rgba(255,255,255,0.35); margin-top: 0.2rem; }

.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem; font-weight: 700; color: #fff;
    margin: 1.5rem 0 1rem 0;
}

.progress-wrap { margin: 0.8rem 0; }
.progress-label {
    display: flex; justify-content: space-between;
    font-size: 0.85rem; color: rgba(255,255,255,0.6); margin-bottom: 0.4rem;
}
.progress-bar-bg { background: rgba(255,255,255,0.1); border-radius: 50px; height: 14px; overflow: hidden; }
.progress-bar-fill-water { height: 100%; border-radius: 50px; background: linear-gradient(90deg, #00d2ff, #0072ff); }
.progress-bar-fill-sleep { height: 100%; border-radius: 50px; background: linear-gradient(90deg, #a18cd1, #fbc2eb); }

.log-entry {
    background: rgba(255,255,255,0.04);
    border-left: 3px solid #00d2ff;
    border-radius: 0 10px 10px 0;
    padding: 0.5rem 1rem; margin: 0.3rem 0;
    color: rgba(255,255,255,0.8); font-size: 0.9rem;
}

.tip-card {
    background: linear-gradient(135deg, rgba(0,210,255,0.1), rgba(123,47,247,0.1));
    border: 1px solid rgba(0,210,255,0.2);
    border-radius: 16px; padding: 1rem 1.2rem; margin: 1rem 0;
    color: rgba(255,255,255,0.85); font-size: 0.9rem;
}
.tip-card strong { color: #00d2ff; }

div.stButton > button {
    background: linear-gradient(135deg, #0072ff, #00d2ff) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; font-weight: 700 !important;
    font-family: 'Nunito', sans-serif !important;
}
div.stButton > button:hover { opacity: 0.85 !important; }

.stNumberInput input, .stTextInput input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important; color: white !important;
}
label { color: rgba(255,255,255,0.7) !important; font-weight: 600 !important; }

.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.05); border-radius: 10px 10px 0 0;
    color: rgba(255,255,255,0.6); font-weight: 700;
}
.stTabs [aria-selected="true"] { background: rgba(0,210,255,0.15) !important; color: #00d2ff !important; }
.stExpander { background: rgba(255,255,255,0.04); border-radius: 12px; border: 1px solid rgba(255,255,255,0.08) !important; }
</style>
""", unsafe_allow_html=True)

# ── Константы ───────────────────────────────────────────────────────────────
DATA_FILE = "data.json"
WATER_GOAL = 2000
SLEEP_GOAL = 8

TIPS = [
    "Выпивай стакан воды сразу после пробуждения — запускает метаболизм.",
    "Кофе и чай не заменяют воду. Учитывай их отдельно.",
    "Сон до полуночи ценнее — с 22:00 до 02:00 идёт восстановление организма.",
    "Поставь стакан воды на рабочий стол — напоминание работает лучше всего.",
    "7–9 часов сна для большинства людей — оптимальный диапазон.",
    "Телефон перед сном снижает качество сна. Откладывай за 30 мин.",
    "Небольшая прогулка после обеда улучшает качество сна ночью.",
]

MOODS = ["😴", "😐", "🙂", "😊", "🤩"]
MOOD_LABELS = ["Разбит", "Норм", "Хорошо", "Отлично", "Энергичен!"]

# ── Данные ───────────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def today_str():
    return str(date.today())

def get_today(data):
    td = today_str()
    if td not in data:
        data[td] = {"water": 0, "sleep": None, "sleep_note": "", "water_log": [], "mood": None}
    for key, default in [("water_log", []), ("mood", None), ("sleep_note", "")]:
        if key not in data[td]:
            data[td][key] = default
    return data[td]

def calc_streak(data):
    streak = 0
    d = date.today()
    for _ in range(365):
        key = str(d)
        if key in data:
            e = data[key]
            if e.get("water", 0) >= WATER_GOAL and (e.get("sleep") or 0) >= SLEEP_GOAL:
                streak += 1
                d -= timedelta(days=1)
            else:
                break
        else:
            break
    return streak

def week_completion(data):
    done = 0
    for i in range(7):
        d = str(date.today() - timedelta(days=i))
        if d in data:
            e = data[d]
            if e.get("water", 0) >= WATER_GOAL and (e.get("sleep") or 0) >= SLEEP_GOAL:
                done += 1
    return done

# ── Загрузка ─────────────────────────────────────────────────────────────────
data = load_data()
today = get_today(data)
streak = calc_streak(data)
week_done = week_completion(data)
tip = TIPS[date.today().toordinal() % len(TIPS)]

# ════ HEADER ════
st.markdown(f"""
<div class="app-header">
  <h1>💧 HealthTrack</h1>
  <p>Трекер воды и сна · {date.today().strftime('%d.%m.%Y')}</p>
</div>
""", unsafe_allow_html=True)

# ════ КАРТОЧКИ ════
c1, c2, c3, c4 = st.columns(4)
water_pct = min(today["water"] / WATER_GOAL, 1.0)
sleep_val = today["sleep"] or 0.0
sleep_pct = min(sleep_val / SLEEP_GOAL, 1.0)

with c1:
    st.markdown(f"""<div class="metric-card">
      <div class="icon">💧</div><div class="value">{today['water']}</div>
      <div class="label">мл сегодня</div>
      <div class="sub">цель {WATER_GOAL} мл {'✅' if today['water'] >= WATER_GOAL else '🔵'}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
      <div class="icon">😴</div><div class="value">{sleep_val:.1f}</div>
      <div class="label">часов сна</div>
      <div class="sub">цель {SLEEP_GOAL} ч {'✅' if sleep_val >= SLEEP_GOAL else '🌙'}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
      <div class="icon">🔥</div><div class="value">{streak}</div>
      <div class="label">дней подряд</div>
      <div class="sub">{'Серия активна!' if streak > 0 else 'Начни сегодня'}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
      <div class="icon">📅</div><div class="value">{week_done}/7</div>
      <div class="label">дней на неделе</div>
      <div class="sub">обе нормы выполнены</div>
    </div>""", unsafe_allow_html=True)

st.markdown(f'<div class="tip-card"><strong>💡 Совет дня:</strong> {tip}</div>', unsafe_allow_html=True)

# ════ ОСНОВНЫЕ КОЛОНКИ ════
left, right = st.columns(2, gap="large")

# ─── ВОДА ───
with left:
    st.markdown('<div class="section-title">💧 Вода</div>', unsafe_allow_html=True)

    fill_w = int(water_pct * 100)
    st.markdown(f"""
    <div class="progress-wrap">
      <div class="progress-label"><span>{today['water']} мл</span><span>{fill_w}%</span></div>
      <div class="progress-bar-bg"><div class="progress-bar-fill-water" style="width:{fill_w}%"></div></div>
      <div class="progress-label" style="margin-top:4px">
        <span style="color:rgba(255,255,255,0.35)">осталось {max(WATER_GOAL - today['water'], 0)} мл</span>
        <span style="color:rgba(255,255,255,0.35)">цель {WATER_GOAL} мл</span>
      </div>
    </div>""", unsafe_allow_html=True)

    if today["water"] >= WATER_GOAL:
        st.success("🎉 Норма воды выполнена!")

    st.write("**Быстрое добавление:**")
    qc = st.columns(4)
    for i, ml in enumerate([150, 200, 300, 500]):
        with qc[i]:
            if st.button(f"💧{ml}", use_container_width=True, key=f"q{ml}"):
                today["water"] += ml
                today["water_log"].append({"time": datetime.now().strftime("%H:%M"), "amount": ml})
                save_data(data); st.rerun()

    wamt = st.number_input("Своё количество (мл)", min_value=0, max_value=3000, step=50, value=250)
    if st.button("➕ Добавить воду", use_container_width=True):
        if wamt > 0:
            today["water"] += wamt
            today["water_log"].append({"time": datetime.now().strftime("%H:%M"), "amount": wamt})
            save_data(data); st.rerun()
        else:
            st.warning("Введи количество больше 0")

    if today["water_log"]:
        with st.expander(f"📋 Лог за сегодня ({len(today['water_log'])} записей)"):
            for e in reversed(today["water_log"]):
                st.markdown(f'<div class="log-entry">🕐 {e["time"]} — <b>{e["amount"]} мл</b></div>', unsafe_allow_html=True)

    if st.button("🗑️ Сбросить воду", key="reset_w"):
        today["water"] = 0; today["water_log"] = []
        save_data(data); st.rerun()

# ─── СОН + НАСТРОЕНИЕ ───
with right:
    st.markdown('<div class="section-title">😴 Сон</div>', unsafe_allow_html=True)

    fill_s = int(sleep_pct * 100)
    st.markdown(f"""
    <div class="progress-wrap">
      <div class="progress-label"><span>{sleep_val:.1f} ч</span><span>{fill_s}%</span></div>
      <div class="progress-bar-bg"><div class="progress-bar-fill-sleep" style="width:{fill_s}%"></div></div>
      <div class="progress-label" style="margin-top:4px">
        <span style="color:rgba(255,255,255,0.35)">цель {SLEEP_GOAL} ч</span>
      </div>
    </div>""", unsafe_allow_html=True)

    st.write("**Быстрый выбор:**")
    sc = st.columns(4)
    for i, h in enumerate([6, 7, 8, 9]):
        with sc[i]:
            if st.button(f"🌙{h}ч", use_container_width=True, key=f"sh{h}"):
                today["sleep"] = float(h); save_data(data); st.rerun()

    s_hours = st.number_input("Часов сна", min_value=0.0, max_value=24.0, step=0.5, value=float(sleep_val))
    s_note = st.text_input("Заметка о сне", value=today.get("sleep_note", ""), placeholder="Плохо засыпал, кошмары...")

    if st.button("💾 Сохранить сон", use_container_width=True):
        today["sleep"] = s_hours; today["sleep_note"] = s_note
        save_data(data); st.success("Сон сохранён!"); st.rerun()

    if sleep_val > 0:
        if sleep_val >= SLEEP_GOAL:
            st.success("✅ Норма сна выполнена!")
        elif sleep_val >= 6:
            st.warning(f"⚠️ Чуть не хватает (норма {SLEEP_GOAL} ч)")
        else:
            st.error("❌ Слишком мало! Постарайся поспать больше")

    st.divider()
    st.markdown('<div class="section-title">🎭 Самочувствие</div>', unsafe_allow_html=True)
    st.write("Как ты себя чувствуешь сегодня?")

    mc = st.columns(5)
    for i, (emoji, label) in enumerate(zip(MOODS, MOOD_LABELS)):
        with mc[i]:
            selected = today.get("mood") == i
            border = "2px solid #00d2ff" if selected else "2px solid transparent"
            st.markdown(f'<div style="text-align:center;font-size:1.8rem;border:{border};border-radius:12px;padding:4px">{emoji}</div>', unsafe_allow_html=True)
            if st.button(label, key=f"mood_{i}", use_container_width=True):
                today["mood"] = i; save_data(data); st.rerun()

    if today.get("mood") is not None:
        m = today["mood"]
        st.info(f"Настроение: {MOODS[m]} {MOOD_LABELS[m]}")

# ════ СТАТИСТИКА ════
st.divider()
st.markdown('<div class="section-title">📊 Статистика за 7 дней</div>', unsafe_allow_html=True)

save_data(data)
keys7 = sorted(data.keys())[-7:]
rows = []
for k in keys7:
    d = data[k]
    rows.append({
        "Дата": k,
        "Вода (мл)": d.get("water", 0),
        "Сон (ч)": d.get("sleep") or 0,
        "Настроение": MOODS[d["mood"]] if d.get("mood") is not None else "—",
    })

if rows:
    df = pd.DataFrame(rows).set_index("Дата")
    tab1, tab2, tab3 = st.tabs(["💧 Вода", "😴 Сон", "📋 Таблица"])
    with tab1:
        st.bar_chart(df[["Вода (мл)"]], color="#00d2ff")
        st.caption(f"Норма: {WATER_GOAL} мл/день")
    with tab2:
        st.bar_chart(df[["Сон (ч)"]], color="#a18cd1")
        st.caption(f"Норма: {SLEEP_GOAL} ч/день")
    with tab3:
        df_show = df.copy()
        df_show["Вода ✅"] = df_show["Вода (мл)"].apply(lambda x: "✅" if x >= WATER_GOAL else "❌")
        df_show["Сон ✅"] = df_show["Сон (ч)"].apply(lambda x: "✅" if x >= SLEEP_GOAL else "❌")
        st.dataframe(df_show, use_container_width=True)
else:
    st.info("Пока нет данных. Начни сегодня!")

st.markdown("""
<div style='text-align:center;color:rgba(255,255,255,0.2);font-size:0.8rem;margin-top:2rem;padding-bottom:2rem'>
  HealthTrack · Хакатон АПЕК ПетроТехник
</div>
""", unsafe_allow_html=True)
