import json
import os
import uuid
from datetime import date, time, datetime

import streamlit as st

# --------------------------
# Config
# --------------------------
st.set_page_config(
    page_title="Tareas",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
PRIORITIES = ["Alta", "Media", "Baja"]
PRIORITY_WEIGHT = {"Alta": 0, "Media": 1, "Baja": 2}
DAY_EMOJI = {
    "Lunes": "🌙", "Martes": "🔥", "Miércoles": "⚡", "Jueves": "🌿",
    "Viernes": "🎉", "Sábado": "☀️", "Domingo": "🌊",
}
PRIO_COLOR = {"Alta": "#FF4D6D", "Media": "#FFB347", "Baja": "#4ECDC4"}
DATA_FILE = "tareas.json"

# --------------------------
# CSS moderno minimalista
# --------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #0F0F13 !important;
    color: #E8E8F0 !important;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding-top: 2.5rem !important;
    max-width: 100% !important;
    padding-left: 3.5rem !important;
    padding-right: 3.5rem !important;
}

/* Métricas */
[data-testid="stMetric"] {
    background: #1A1A24 !important;
    border: 1px solid #2A2A38 !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.4rem !important;
}
[data-testid="stMetricLabel"] { color: #888899 !important; font-size: 0.78rem !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }
[data-testid="stMetricValue"] { color: #E8E8F0 !important; font-size: 2rem !important; font-weight: 700 !important; }

/* Progress bar */
[data-testid="stProgressBar"] > div { background: #1A1A24 !important; border-radius: 99px !important; height: 6px !important; }
[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg, #7C6EFA, #B06EFA) !important; border-radius: 99px !important; }

/* Botones primarios */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7C6EFA 0%, #B06EFA 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0.45rem 1.2rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button[kind="primary"]:hover { opacity: 0.85 !important; }

/* Botones secundarios */
.stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    background: #1A1A24 !important;
    border: 1px solid #2A2A38 !important;
    color: #AAAACC !important;
}
.stButton > button:hover { border-color: #7C6EFA !important; color: #7C6EFA !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #1A1A24 !important;
    border: 1px solid #2A2A38 !important;
    border-radius: 10px !important;
    color: #E8E8F0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Containers / cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #141420 !important;
    border: 1px solid #22223A !important;
    border-radius: 16px !important;
    padding: 0.2rem 0.8rem !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #1A1A24 !important;
    border: 1px solid #2A2A38 !important;
    border-radius: 12px !important;
}

/* Divider */
hr { border-color: #22223A !important; }

/* Caption */
.stCaption { color: #666680 !important; font-size: 0.78rem !important; }

/* Day filter pills — selectbox accent */
.stSelectbox [data-baseweb="select"] > div { border-radius: 10px !important; }

/* Tag prioridad */
.prio-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# --------------------------
# Helpers
# --------------------------
def day_index(day: str) -> int:
    try:
        return DAYS.index(day)
    except ValueError:
        return 999

def get_today_day_name() -> str:
    """Retorna el nombre del día en español según el día actual."""
    weekday = datetime.today().weekday()  # 0=Monday
    return DAYS[weekday] if weekday < len(DAYS) else "Lunes"

def parse_hhmm(s: str) -> time:
    try:
        hh, mm = s.split(":")
        return time(int(hh), int(mm))
    except Exception:
        return time(0, 0)

def hhmm(t: time) -> str:
    return f"{t.hour:02d}:{t.minute:02d}"

def load_tasks() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for i, task in enumerate(data):
                task.setdefault("id", str(uuid.uuid4()))
                task.setdefault("title", "")
                task.setdefault("desc", "")
                task.setdefault("day", "Lunes")
                task.setdefault("priority", "Media")
                task.setdefault("time", "00:00")
                task.setdefault("done", False)
                task.setdefault("order", i)
            return data
        return []
    except Exception:
        return []

def save_tasks(tasks: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def sort_tasks(tasks: list[dict], mode: str = "day") -> list[dict]:
    if mode == "day":
        return sorted(tasks, key=lambda t: (
            day_index(t.get("day", "")),
            parse_hhmm(t.get("time", "00:00")),
            PRIORITY_WEIGHT.get(t.get("priority", "Media"), 99),
            int(t.get("order", 0)),
        ))
    else:
        return sorted(tasks, key=lambda t: (
            PRIORITY_WEIGHT.get(t.get("priority", "Media"), 99),
            day_index(t.get("day", "")),
            parse_hhmm(t.get("time", "00:00")),
            int(t.get("order", 0)),
        ))

def next_order(tasks: list[dict]) -> int:
    if not tasks:
        return 0
    return max(int(t.get("order", 0)) for t in tasks) + 1

def get_iso_week() -> str:
    return str(date.today().isocalendar()[:2])  # e.g. "(2026, 9)"

def get_last_reset() -> str:
    if os.path.exists("last_reset.txt"):
        try:
            return open("last_reset.txt").read().strip()
        except Exception:
            return ""
    return ""

def save_last_reset(w: str) -> None:
    with open("last_reset.txt", "w") as f:
        f.write(w)

# --------------------------
# Session state
# --------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()
if "form_gen" not in st.session_state:
    st.session_state.form_gen = 0

# ── WEEKLY RESET (lunes de cada semana) ───────────────────────────────────────
current_week = get_iso_week()
if get_last_reset() != current_week:
    changed = False
    for t in st.session_state.tasks:
        if t.get("done", False):
            t["done"] = False
            changed = True
    if changed:
        save_tasks(st.session_state.tasks)
    save_last_reset(current_week)
# ─────────────────────────────────────────────────────────────────────────────

tasks = st.session_state.tasks
today_day = get_today_day_name()

# --------------------------
# Derived counts
# --------------------------
total         = len(tasks)
done_count    = sum(1 for t in tasks if t.get("done"))
pending_count = total - done_count
pct_done      = int(done_count / total * 100) if total > 0 else 0
pct_pending   = int(pending_count / total * 100) if total > 0 else 0

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
st.markdown(f"""
<div style="margin-bottom:0.2rem">
  <span style="font-size:2rem;font-weight:700;letter-spacing:-0.03em;color:#E8E8F0;">◈ Mis Tareas</span><br>
  <span style="color:#555570;font-size:0.85rem;font-weight:400;">
    {DAY_EMOJI.get(today_day, '📅')} Hoy es <b style="color:#7C6EFA">{today_day}</b> · semana {date.today().isocalendar()[1]}
  </span>
</div>
""", unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════
# METRIC CARDS
# ══════════════════════════════════════════════
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("◻ Total", total)
with m2:
    st.metric("⏳ Pendientes", pending_count, delta=f"{pct_pending}%", delta_color="off")
with m3:
    st.metric("✓ Completadas", done_count, delta=f"{pct_done}%", delta_color="normal")

if total > 0:
    st.progress(pct_done / 100, text=f"Progreso semanal · {pct_done}%")

st.divider()

# ══════════════════════════════════════════════
# ADD TASK FORM
# ══════════════════════════════════════════════
g = st.session_state.form_gen

with st.expander("＋  Nueva tarea", expanded=False):
    c1, c2, c3 = st.columns([3, 1.2, 1.2])
    title    = c1.text_input("Tarea", placeholder="Ej: Publicar diseño en Etsy", key=f"form_title_{g}", label_visibility="collapsed")
    desc     = c1.text_area("Descripción", placeholder="Detalles, pasos, notas…", height=72, key=f"form_desc_{g}", label_visibility="collapsed")
    day      = c2.selectbox("Día", DAYS, index=day_index(today_day), key=f"form_day_{g}")
    priority = c3.selectbox("Prioridad", PRIORITIES, index=1, key=f"form_priority_{g}")
    col_t, _ = st.columns([2, 3])
    task_time = col_t.time_input("Hora", value=time(8, 0), key=f"form_time_{g}")

    if st.button("Crear tarea →", type="primary"):
        if not title.strip():
            st.warning("Escribe un título para la tarea.")
        else:
            tasks.append({
                "id": str(uuid.uuid4()),
                "title": title.strip(),
                "desc": desc.strip(),
                "day": day,
                "priority": priority,
                "time": hhmm(task_time),
                "done": False,
                "order": next_order(tasks),
            })
            save_tasks(tasks)
            st.session_state.form_gen += 1
            st.rerun()

st.divider()

# ══════════════════════════════════════════════
# FILTERS — día actual por defecto
# ══════════════════════════════════════════════
st.markdown("<span style='font-size:1rem;font-weight:600;color:#888899;letter-spacing:0.06em;text-transform:uppercase;'>Tareas</span>", unsafe_allow_html=True)

f1, f2, f3, f4 = st.columns([1.2, 1.2, 1, 1.8])

# ← DÍA DE HOY como default
today_index_in_filter = DAYS.index(today_day) + 1  # +1 porque index 0 = "Todos"
filter_day      = f1.selectbox("Día", ["Todos"] + DAYS, index=today_index_in_filter)
filter_priority = f2.selectbox("Prioridad", ["Todas"] + PRIORITIES, index=0)
show_done       = f3.checkbox("Ver hechas", value=True)
sort_mode       = f4.selectbox("Ordenar por", ["Día → Hora → Prioridad", "Prioridad → Día → Hora"], index=0)

filtered = tasks[:]
if filter_day      != "Todos":  filtered = [t for t in filtered if t.get("day")      == filter_day]
if filter_priority != "Todas":  filtered = [t for t in filtered if t.get("priority") == filter_priority]
if not show_done:               filtered = [t for t in filtered if not t.get("done", False)]

mode_key = "day" if "Día" in sort_mode else "priority"
filtered = sort_tasks(filtered, mode=mode_key)

n = len(filtered)
st.caption(f'{n} tarea{"s" if n != 1 else ""} · reseteo semanal los lunes')

# ══════════════════════════════════════════════
# RENDER TASKS
# ══════════════════════════════════════════════
PRIO_ICON = {"Alta": "●", "Media": "●", "Baja": "●"}

if not filtered:
    st.markdown("""
    <div style="text-align:center;padding:3rem 0;color:#333350;">
        <div style="font-size:2.5rem;margin-bottom:0.5rem;">◈</div>
        <div style="font-size:0.95rem;">Sin tareas aquí. Agrega una o cambia el filtro.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for t in filtered:
        done      = bool(t.get("done", False))
        prio      = t.get("priority", "Media")
        prio_color = PRIO_COLOR.get(prio, "#888")
        day_emoji = DAY_EMOJI.get(t.get("day", ""), "📅")
        title_txt = t.get("title", "")
        opacity   = "0.45" if done else "1"

        with st.container(border=True):
            st.markdown(f"""
            <div style="opacity:{opacity};display:flex;align-items:center;gap:10px;padding:0.1rem 0 0.4rem 0;">
                <span style="color:{prio_color};font-size:0.7rem;">●</span>
                <span style="font-size:0.72rem;color:#555570;font-family:'DM Mono',monospace;letter-spacing:0.03em;">
                    {day_emoji} {t.get('day')} · {t.get('time')}
                </span>
                <span style="font-size:0.95rem;font-weight:{'400' if done else '600'};
                    {'text-decoration:line-through;color:#444460' if done else 'color:#E8E8F0'}">
                    {title_txt}
                </span>
            </div>
            """, unsafe_allow_html=True)

            col_check, col_del, col_edit = st.columns([1.5, 0.8, 3])

            with col_check:
                done_value = st.checkbox(
                    "✓ Hecha" if done else "Marcar hecha",
                    value=done,
                    key=f"done_{t['id']}"
                )
                if done_value != done:
                    for tt in tasks:
                        if tt["id"] == t["id"]:
                            tt["done"] = done_value
                            break
                    save_tasks(tasks)
                    st.rerun()

            with col_del:
                if st.button("✕", key=f"qdel_{t['id']}", help="Eliminar tarea"):
                    st.session_state.tasks = [x for x in tasks if x["id"] != t["id"]]
                    save_tasks(st.session_state.tasks)
                    st.rerun()

            with col_edit:
                with st.expander("Editar"):
                    if t.get("desc"):
                        st.caption(t.get("desc"))

                    e1, e2, e3 = st.columns([3, 1.2, 1.2])
                    new_title    = e1.text_input("Título",     value=t.get("title",""),  key=f"etitle_{t['id']}")
                    new_desc     = e1.text_area("Descripción", value=t.get("desc",""),   height=68, key=f"edesc_{t['id']}")
                    new_day      = e2.selectbox("Día",       DAYS,       index=day_index(t.get("day","Lunes")), key=f"eday_{t['id']}")
                    new_priority = e3.selectbox("Prioridad", PRIORITIES, index=PRIORITIES.index(t.get("priority","Media")), key=f"eprio_{t['id']}")
                    new_time     = st.time_input("Hora", value=parse_hhmm(t.get("time","00:00")), key=f"etime_{t['id']}")

                    if st.button("Guardar →", type="primary", key=f"save_{t['id']}"):
                        for tt in tasks:
                            if tt["id"] == t["id"]:
                                tt.update({
                                    "title": new_title.strip(),
                                    "desc": new_desc.strip(),
                                    "day": new_day,
                                    "priority": new_priority,
                                    "time": hhmm(new_time),
                                })
                                break
                        save_tasks(tasks)
                        st.rerun()

# ══════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════
st.divider()
st.caption("◈ tareas.json · reset semanal automático cada lunes · sin internet requerido")
