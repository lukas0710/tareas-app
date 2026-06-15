import json
import os
import uuid
import base64
import urllib.request
import urllib.error
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
# Almacenamiento (GitHub si hay token, si no archivo local)
# --------------------------
def _secret(key, default=""):
    """Lee un valor de st.secrets sin romper si no existe."""
    try:
        return st.secrets[key]
    except Exception:
        return default

GH_TOKEN  = _secret("GITHUB_TOKEN", "")
GH_REPO   = _secret("GITHUB_REPO", "lukas0710/tareas-app")
GH_BRANCH = _secret("GITHUB_BRANCH", "main")
GH_PATH   = _secret("GITHUB_PATH", "tareas.json")
USE_GITHUB = bool(GH_TOKEN and GH_REPO)


def _gh_request(url, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {GH_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "tareas-app")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _gh_load_raw():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_PATH}?ref={GH_BRANCH}"
    info = _gh_request(url)
    st.session_state._gh_sha = info.get("sha")
    content = base64.b64decode(info["content"]).decode("utf-8")
    return json.loads(content)


def _gh_save_raw(obj):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_PATH}"
    body = json.dumps(obj, ensure_ascii=False, indent=2)
    payload = {
        "message": "Actualizar tareas desde la app",
        "content": base64.b64encode(body.encode("utf-8")).decode("utf-8"),
        "branch": GH_BRANCH,
    }
    sha = st.session_state.get("_gh_sha")
    if sha:
        payload["sha"] = sha
    resp = _gh_request(url, method="PUT", payload=payload)
    st.session_state._gh_sha = resp["content"]["sha"]


def _normalize(raw):
    """Acepta lista (formato viejo) o dict (formato nuevo) -> (tasks, meta)."""
    if isinstance(raw, dict):
        tasks = raw.get("tasks", [])
        meta = {"last_reset": raw.get("last_reset", "")}
    elif isinstance(raw, list):
        tasks = raw
        meta = {"last_reset": ""}
    else:
        tasks, meta = [], {"last_reset": ""}

    if not isinstance(tasks, list):
        tasks = []

    for i, t in enumerate(tasks):
        t.setdefault("id", str(uuid.uuid4()))
        t.setdefault("title", "")
        t.setdefault("desc", "")
        t.setdefault("day", "Lunes")
        t.setdefault("priority", "Media")
        t.setdefault("time", "00:00")
        t.setdefault("done", False)
        t.setdefault("order", i)
        t.setdefault("recurring", True)   # las tareas viejas son rutina
    return tasks, meta


def storage_load():
    if USE_GITHUB:
        try:
            return _normalize(_gh_load_raw())
        except Exception as e:
            st.session_state._storage_error = f"No se pudo leer de GitHub: {e}"
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return _normalize(json.load(f))
        except Exception:
            pass
    return _normalize([])


def storage_save():
    obj = {
        "tasks": st.session_state.tasks,
        "last_reset": st.session_state.meta.get("last_reset", ""),
    }
    # Copia local siempre (es lo que se usa al correrla en tu PC)
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # Guardado permanente en GitHub si hay token
    if USE_GITHUB:
        try:
            _gh_save_raw(obj)
            st.session_state._storage_error = ""
        except Exception as e:
            st.session_state._storage_error = f"No se pudo guardar en GitHub: {e}"


def persist():
    storage_save()

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

# --------------------------
# Session state
# --------------------------
if "tasks" not in st.session_state or "meta" not in st.session_state:
    st.session_state.tasks, st.session_state.meta = storage_load()
if "form_gen" not in st.session_state:
    st.session_state.form_gen = 0

# ── RESET SEMANAL (solo tareas recurrentes) ───────────────────────────────────
# Las tareas "únicas" NO se reinician: se quedan hasta que las completes.
current_week = get_iso_week()
if st.session_state.meta.get("last_reset") != current_week:
    for t in st.session_state.tasks:
        if t.get("recurring", True) and t.get("done", False):
            t["done"] = False
    st.session_state.meta["last_reset"] = current_week
    persist()
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

# Indicador de guardado
if USE_GITHUB:
    if st.session_state.get("_storage_error"):
        st.warning("⚠️ " + st.session_state._storage_error)
    else:
        st.caption("💾 Guardado permanente activo (GitHub)")
else:
    st.caption("💾 Guardado local · en la nube las tareas pueden borrarse al reiniciar. Activa el guardado en GitHub (ver instrucciones).")

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
    st.progress(pct_done / 100, text=f"Progreso · {pct_done}%")

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

    col_t, col_r = st.columns([2, 3])
    task_time = col_t.time_input("Hora", value=time(8, 0), key=f"form_time_{g}")
    recurring = col_r.toggle("🔁 Se repite cada semana", value=True, key=f"form_recurring_{g}")
    if recurring:
        col_r.caption("Rutina: cada lunes se reinicia para volver a hacerla.")
    else:
        col_r.caption("Tarea única: queda pendiente hasta que la completes (no se borra).")

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
                "recurring": bool(recurring),
                "order": next_order(tasks),
            })
            persist()
            st.session_state.form_gen += 1
            st.rerun()

st.divider()

# ══════════════════════════════════════════════
# FILTERS — día actual por defecto
# ══════════════════════════════════════════════
st.markdown("<span style='font-size:1rem;font-weight:600;color:#888899;letter-spacing:0.06em;text-transform:uppercase;'>Tareas</span>", unsafe_allow_html=True)

f1, f2, f3, f4, f5 = st.columns([1.2, 1.2, 1.2, 1, 1.6])

# ← DÍA DE HOY como default
today_index_in_filter = DAYS.index(today_day) + 1  # +1 porque index 0 = "Todos"
filter_day      = f1.selectbox("Día", ["Todos"] + DAYS, index=today_index_in_filter)
filter_type     = f2.selectbox("Tipo", ["Todas", "🔁 Recurrentes", "📌 Únicas"], index=0)
filter_priority = f3.selectbox("Prioridad", ["Todas"] + PRIORITIES, index=0)
show_done       = f4.checkbox("Ver hechas", value=True)
sort_mode       = f5.selectbox("Ordenar por", ["Día → Hora → Prioridad", "Prioridad → Día → Hora"], index=0)

filtered = tasks[:]
if filter_day      != "Todos":  filtered = [t for t in filtered if t.get("day")      == filter_day]
if filter_priority != "Todas":  filtered = [t for t in filtered if t.get("priority") == filter_priority]
if filter_type == "🔁 Recurrentes":  filtered = [t for t in filtered if t.get("recurring", True)]
elif filter_type == "📌 Únicas":     filtered = [t for t in filtered if not t.get("recurring", True)]
if not show_done:               filtered = [t for t in filtered if not t.get("done", False)]

mode_key = "day" if "Día" in sort_mode else "priority"
filtered = sort_tasks(filtered, mode=mode_key)

n = len(filtered)
st.caption(f'{n} tarea{"s" if n != 1 else ""} · las recurrentes se reinician los lunes · las únicas quedan hasta completarlas')

# Botón para limpiar tareas únicas completadas
done_unique = [t for t in tasks if not t.get("recurring", True) and t.get("done", False)]
if done_unique:
    if st.button(f"🧹 Limpiar {len(done_unique)} tarea(s) única(s) completada(s)"):
        st.session_state.tasks = [
            t for t in tasks
            if not (not t.get("recurring", True) and t.get("done", False))
        ]
        persist()
        st.rerun()

# ══════════════════════════════════════════════
# RENDER TASKS
# ══════════════════════════════════════════════
if not filtered:
    st.markdown("""
    <div style="text-align:center;padding:3rem 0;color:#333350;">
        <div style="font-size:2.5rem;margin-bottom:0.5rem;">◈</div>
        <div style="font-size:0.95rem;">Sin tareas aquí. Agrega una o cambia el filtro.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for t in filtered:
        done       = bool(t.get("done", False))
        prio       = t.get("priority", "Media")
        prio_color = PRIO_COLOR.get(prio, "#888")
        day_emoji  = DAY_EMOJI.get(t.get("day", ""), "📅")
        title_txt  = t.get("title", "")
        opacity    = "0.45" if done else "1"
        is_rec     = t.get("recurring", True)
        type_badge = "🔁" if is_rec else "📌"

        with st.container(border=True):
            st.markdown(f"""
            <div style="opacity:{opacity};display:flex;align-items:center;gap:10px;padding:0.1rem 0 0.4rem 0;">
                <span style="color:{prio_color};font-size:0.7rem;">●</span>
                <span style="font-size:0.72rem;color:#555570;font-family:'DM Mono',monospace;letter-spacing:0.03em;">
                    {type_badge} {day_emoji} {t.get('day')} · {t.get('time')}
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
                    persist()
                    st.rerun()

            with col_del:
                if st.button("✕", key=f"qdel_{t['id']}", help="Eliminar tarea"):
                    st.session_state.tasks = [x for x in tasks if x["id"] != t["id"]]
                    persist()
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
                    new_recurring = st.toggle("🔁 Se repite cada semana", value=bool(t.get("recurring", True)), key=f"erec_{t['id']}")

                    if st.button("Guardar →", type="primary", key=f"save_{t['id']}"):
                        for tt in tasks:
                            if tt["id"] == t["id"]:
                                tt.update({
                                    "title": new_title.strip(),
                                    "desc": new_desc.strip(),
                                    "day": new_day,
                                    "priority": new_priority,
                                    "time": hhmm(new_time),
                                    "recurring": bool(new_recurring),
                                })
                                break
                        persist()
                        st.rerun()

# ══════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════
st.divider()
st.caption("◈ 🔁 recurrente = rutina semanal · 📌 única = queda hasta completarla")




