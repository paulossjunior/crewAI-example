"""Streamlit chat UI for the Dinner Pairing Crew.

Run with::

    uv run streamlit run src/dinner_crew/app.py

The user asks for a dinner in free text; ``RequestParser`` turns the message into a
``DinnerRequest`` (kept across messages, editable in the sidebar). Two modes:

- **Sem IA**: the three recommenders run; a template writes the host summary and the plan. Offline.
- **Com IA**: the CrewAI crew (three specialists + the host, OpenAI) writes the plan.

A sidebar switch picks the dataset: ``toy`` (hand-written) or ``large`` (generated).
"""

from __future__ import annotations

import os
import uuid

import streamlit as st
from dotenv import load_dotenv

from dinner_crew.data import DATASETS, dataset_dir
from dinner_crew.intake import DinnerRequest, RequestParser
from dinner_crew.models import PRICES, RESTRICTIONS
from dinner_crew.pipeline import Recommenders, build_crew_inputs, render_plan, run_recommenders

MODE_OFFLINE = "Sem IA (offline)"
MODE_AI = "Com IA (CrewAI + OpenAI)"
NEW_USER = "(novo usuário)"
GREETING = (
    "Olá! Me diga o que você quer jantar. Exemplos:\n\n"
    "- *quero um prato vegetariano com cogumelos*\n"
    "- *algo com carne grelhada, sou u3*\n"
    "- *e um vinho mais barato?*"
)

load_dotenv()
st.set_page_config(page_title="Dinner Pairing Crew", page_icon="🍽️")


@st.cache_resource
def get_recommenders(dataset: str) -> Recommenders:
    return Recommenders(dataset)


@st.cache_resource
def get_parser(dataset: str) -> RequestParser:
    return RequestParser(dataset_dir(dataset))


def sidebar_request() -> DinnerRequest:
    """Current request as shown (and possibly edited) in the sidebar."""
    s = st.session_state
    return DinnerRequest(
        preferences=list(s.get("preferences", [])),
        restrictions=list(s.get("restrictions", [])),
        price=s.get("price", "media"),
        city=s.get("city", "São Paulo"),
        user_id=None if s.get("user", NEW_USER) == NEW_USER else s.get("user"),
        dish=s.get("dish"),
    )


def store_request(req: DinnerRequest) -> None:
    """Write a request into the sidebar widgets' state (must run before they are drawn)."""
    s = st.session_state
    s["preferences"], s["restrictions"], s["price"] = req.preferences, req.restrictions, req.price
    s["city"], s["user"], s["dish"] = req.city, req.user_id or NEW_USER, req.dish


CREW_STEPS = [
    "🍽️ Food Sommelier escolhendo o prato (LightFM)",
    "🍷 Wine Sommelier harmonizando o vinho (implicit)",
    "📍 Concierge procurando o restaurante (Surprise)",
    "🗣️ Anfitrião escrevendo o resumo",
]


def run_crew_with_progress(crew, inputs: dict, req: DinnerRequest, dataset: str) -> str:
    """Run the crew while showing which agent is working.

    ``kickoff`` blocks for ~30-60 s (four LLM calls). Without feedback the page looks frozen, and
    users tend to type or click, which makes Streamlit rerun the script and abort the crew. The
    crew's ``task_callback`` runs in this same script thread, so it can update the status box.
    """
    from dinner_crew.observability import kickoff_traced

    with st.status("Os agentes estão trabalhando (~40 s)...", expanded=True) as status:
        st.caption("Aguarde: enviar outra mensagem ou mudar filtros agora interrompe a crew.")
        status.write(CREW_STEPS[0] + "…")
        done = []

        def on_task_done(output) -> None:
            done.append(output)
            status.write(f"✅ {output.agent} concluiu")
            if len(done) < len(CREW_STEPS):
                status.write(CREW_STEPS[len(done)] + "…")

        crew.task_callback = on_task_done
        try:
            output = kickoff_traced(crew, inputs, user_id=req.user_id, session_id=s["session_id"],
                                    tags=["streamlit", dataset])
        except Exception as exc:  # network errors, timeouts, rate limits
            status.update(label="A crew falhou", state="error")
            return f"⚠️ A crew falhou: `{type(exc).__name__}: {exc}`"
        status.update(label="Plano pronto!", state="complete", expanded=False)
    return output.raw


def answer(req: DinnerRequest, mode: str, dataset: str) -> tuple[str, dict]:
    """Produce the assistant reply (markdown) and the raw recommender output."""
    result = run_recommenders(req, get_recommenders(dataset))
    if mode == MODE_AI and result["chosen_dish"]:
        if not os.getenv("OPENAI_API_KEY"):
            return "⚠️ Defina `OPENAI_API_KEY` no `.env` para o modo com IA.\n\n" + render_plan(result, req), result
        from dinner_crew.crew import DinnerCrew  # lazy: crewai import is slow

        os.environ["DINNER_DATASET"] = dataset  # the crew's tools read the dataset from here

        req_for_crew = req if req.dish else DinnerRequest(**{**req.__dict__, "dish": result["chosen_dish"]})
        return run_crew_with_progress(DinnerCrew().crew(), build_crew_inputs(req_for_crew), req, dataset), result
    return render_plan(result, req), result


s = st.session_state
s.setdefault("session_id", uuid.uuid4().hex)  # groups this chat's traces in Langfuse
s.setdefault("messages", [{"role": "assistant", "content": GREETING}])
# Same defaults as the CLI (DinnerRequest). Without them, a radio/selectbox drawn before its key
# exists falls back to its first option — the price would silently start as "baixa".
_DEFAULTS = DinnerRequest()
s.setdefault("price", _DEFAULTS.price)
s.setdefault("city", _DEFAULTS.city)
s.setdefault("user", NEW_USER)

# A submitted chat message is available here, before the sidebar is drawn, so parsing it can
# update the sidebar widgets in this same run.
dataset = s.get("dataset", "toy")
pending = s.pop("chat_input", None)
if pending:
    parsed = get_parser(dataset).parse(pending, sidebar_request())
    store_request(parsed.request)

recs = get_recommenders(dataset)
users = sorted(recs.restaurant.rated)
cities = sorted({r["city"] for r in recs.restaurant.restaurants})
vocab = sorted(get_parser(dataset).vocab)
# After switching datasets, drop sidebar values that do not exist in the new one.
if s.get("user", NEW_USER) not in (NEW_USER, *users):
    s["user"] = NEW_USER
if s.get("city") not in cities:
    s["city"] = "São Paulo" if "São Paulo" in cities else cities[0]
s["preferences"] = [p for p in s.get("preferences", []) if p in vocab]
if s.get("dish") and s["dish"] not in recs.dishes:
    s["dish"] = None

with st.sidebar:
    st.header("Seu jantar")
    mode = st.radio("Modo", [MODE_OFFLINE, MODE_AI], key="mode")
    st.radio("Base de dados", list(DATASETS), key="dataset", horizontal=True,
             format_func=lambda d: {"toy": "toy (pequena)", "large": "large (grande)"}[d])
    st.caption(f"{len(recs.dishes)} pratos · {len(recs.wine.wines)} vinhos · "
               f"{len(recs.restaurant.restaurants)} restaurantes · {len(users)} usuários")
    st.selectbox("Usuário", [NEW_USER, *users], key="user")
    st.selectbox("Cidade", cities, key="city")
    st.radio("Faixa de preço", PRICES, key="price", horizontal=True)
    st.multiselect("Restrições", RESTRICTIONS, key="restrictions", placeholder="Nenhuma")
    st.multiselect("Preferências", vocab, key="preferences", placeholder="Escolha termos ou escreva no chat")
    if s.get("dish"):
        st.caption(f"Prato fixado: **{s['dish']}**")
    if st.button("Recomendar com estes filtros"):
        pending = pending or "(filtros do painel)"
    if st.button("Nova conversa"):
        for key in ("messages", "preferences", "restrictions", "dish", "user", "price", "city"):
            s.pop(key, None)
        st.rerun()

st.title("🍽️ Dinner Pairing Crew")
st.caption("Três especialistas (LightFM · implicit · Surprise) e um anfitrião que resume tudo")

if pending:
    req = sidebar_request()
    s.messages.append({"role": "user", "content": pending})
    understood = parsed.understood if pending != "(filtros do painel)" else ["filtros do painel"]
    if mode == MODE_AI:
        reply, raw = answer(req, mode, dataset)  # shows its own progress box
    else:
        with st.spinner("Recomendando..."):
            reply, raw = answer(req, mode, dataset)
    prefix = f"_Entendi: {'; '.join(understood) or 'nada novo, usei o pedido anterior'}._\n\n"
    s.messages.append({"role": "assistant", "content": prefix + reply, "raw": raw})

for msg in s.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("raw"):
            with st.expander("Ver saída dos recomendadores (JSON)"):
                st.json(msg["raw"])

st.chat_input("O que você quer jantar?", key="chat_input")
