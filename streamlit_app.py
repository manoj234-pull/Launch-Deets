"""Launch-Deets launch research. Run: python -m streamlit run streamlit_app.py."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from html import escape
from pathlib import Path
from time import perf_counter
import sys
import re

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from launch_deets.agent import ask
from launch_deets.config import Settings
from launch_deets.data import load_archive
from launch_deets.trace import RunTrace
from ui.visual import hero_html, launch_html
from ui.entrance import entrance_html

st.set_page_config(page_title="Launch-Deets | Launch research", page_icon="◈", layout="wide")
st.set_option("client.toolbarMode", "minimal")
st.markdown("<style>" + (ROOT / "ui/style.css").read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)

@st.cache_resource
def workers():
    return ThreadPoolExecutor(max_workers=2, thread_name_prefix="launch-deets-ui")

@st.cache_resource
def archive_data():
    return load_archive()


def snapshot(trace):
    with trace._lock:
        return deepcopy(trace.events), deepcopy(trace.usage_rows)


def execute(question, trace, archive, scope="All launches"):
    started = perf_counter()
    try:
        scoped_question = question if scope == "All launches" else question + "\nLimit this question to launch " + scope + "."
        result = ask(scoped_question, archive=archive, settings=Settings.from_env(), trace=trace)
    except Exception as exc:
        # Provider exception messages can contain request details; never render them.
        result = {"status": "error", "message": "A service could not complete this request. Please try again shortly. If the problem continues, contact your administrator.", "error_type": type(exc).__name__}
    return {"question": question, "scope": scope, "result": result, "seconds": perf_counter() - started}


def display_answer(answer):
    """Hide source markers in the UI; preserve the original answer and source checks."""
    source = r"(?:(?:REC|DOC)-L7-\d+|records\.csv)"
    markers = rf"(?:\[\s*{source}(?:\s*[,;]\s*{source})*\s*\]|\(\s*{source}(?:\s*[,;]\s*{source})*\s*\))"
    text = re.sub(markers, "", answer)
    text = re.sub(r"[ \t]+([.,;:!?])", r"\1", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def activity(events):
    selected = set()
    for event in events:
        if event["stage"] == "tool_calls":
            selected.update(call["name"] for call in event.get("calls", []))
    stages = {event["stage"] for event in events}
    if "tool_results" in stages:
        return selected, "Preparing your answer"
    if "tool_calls" in stages:
        return selected, "Connecting relevant information"
    return selected, "Understanding your question"


def hero_art():
    st.iframe(hero_html(), height=390)


def footer():
    st.markdown('<div class="site-footer"><b>launch-deets<span> / launch research</span></b><span>Fictional demonstration archive · Not for operational decisions</span></div>', unsafe_allow_html=True)


def home():
    with st.container(key="home_hero"):
        left, right = st.columns([1.15, 1], vertical_alignment="center")
        with left:
            st.markdown('<div class="eyebrow">LAUNCH RESEARCH, CONNECTED</div><h1 class="hero-title">The full story.<br>Beyond the incident.</h1><p class="hero-copy">Launch-Deets helps you understand past launch incidents. Ask a question in plain language to find what happened, what changed in later reports, and which corrective action was recorded.</p>', unsafe_allow_html=True)
            if st.button("Open research workspace →", type="primary", key="home_cta"):
                st.switch_page(research_page)
            st.markdown('<div class="hero-footnote">Built for exploring incident history and understanding what changed.</div>', unsafe_allow_html=True)
        with right:
            hero_art()
    st.markdown('<div class="intro-row"><div class="eyebrow">A CLEARER WAY TO REVIEW</div><h2>One question. A connected view.</h2><p>Instead of opening separate records and reports, ask Launch-Deets to connect the information for you. It searches the fictional launch archive and returns a readable answer based on the information in the archive.</p></div>', unsafe_allow_html=True)
    cols = st.columns(3)
    cards = [
        ("01 / EVENT RECORDS", "Find the exact detail.", "Review incident counts, measured values and launch-specific facts without searching through individual records."),
        ("02 / INCIDENT REPORTS", "Understand what changed.", "Explore the narrative behind an event and distinguish preliminary findings from later revisions."),
        ("03 / CONNECTED EVENTS", "Follow the corrective action.", "Connect a component to its incident and the recorded action taken to address it.")]
    for col, (label, title, body) in zip(cols, cards):
        with col:
            st.markdown(f'<article class="feature-card"><div class="card-number">{label}</div><h3>{title}</h3><p>{body}</p></article>', unsafe_allow_html=True)
    with st.container(key="home_scope"):
        st.markdown('### Know what the archive can tell you.')
        st.write("Ask about historical events, compare findings and explore recorded fixes. Answers are based on the information available in the archive. When the archive does not contain enough information, the application tells you.")
        st.caption("This demonstration uses fictional Launch-Deets launch data. It does not assess real launch safety or provide operating instructions.")
    st.markdown("## Get familiar with Launch-Deets")
    overview, steps, limits = st.tabs(["What can I find?", "How do I use it?", "What if information is missing?"])
    with overview:
        st.write("Explore incident details, compare preliminary and final findings, and connect affected components to recorded fixes. Use Launch scope to focus on one launch or choose All launches for a wider question.")
    with steps:
        st.markdown("1. Open **Research** and choose a launch scope.\n2. Enter a complete question and select **Start research**.\n3. Read the answer below your question.\n4. Use **Clear question** when you are ready to begin again.")
    with limits:
        st.write("If the archive does not contain enough evidence, Launch-Deets says so instead of filling in missing facts. Try a more specific question or a different launch scope.")
        st.write("This is a demonstration using fictional launch data. It is not a source of real-world operating instructions or launch-safety decisions.")
    footer()


def clear_question():
    st.session_state.question = ""
    st.session_state.pop("current", None)


def research():
    st.session_state.setdefault("question", "")
    busy = "job" in st.session_state
    archive = archive_data()
    st.markdown('<section class="research-banner"><div class="eyebrow">LAUNCH-DEETS / CONNECTED INTELLIGENCE</div><h1>Research. Resolve.<br>See the full picture.</h1><p>A focused workspace for incident history, revised findings and corrective actions.</p><div class="banner-tags"><span>LAUNCH ARCHIVE</span><span>ARCHIVE-BASED ANSWERS</span><span>FICTIONAL DEMONSTRATION</span></div></section>', unsafe_allow_html=True)
    with st.container(key="workspace_controls"):
        scope_col, clear_col = st.columns([3, 1], vertical_alignment="bottom")
        with scope_col:
            scope = st.selectbox("Launch scope", ["All launches"] + sorted(archive.records.launch_id.unique().tolist()), key="launch_scope", disabled=busy,
                                 help="Limits your next question to the selected launch. All launches allows comparisons across the archive.")
        with clear_col:
            st.button("Clear question", on_click=clear_question, disabled=busy, use_container_width=True)
    # One fragment owns both columns, so live updates stay aligned and do not accumulate.
    @st.fragment(run_every="1s" if busy else None)
    def workspace():
        active = "job" in st.session_state
        events = []
        if active:
            job = st.session_state.job
            events, _ = snapshot(job["trace"])
            if job["future"].done():
                st.session_state.current = job["future"].result()
                del st.session_state.job
                st.rerun()
        st.markdown('<div id="research-workspace"></div>', unsafe_allow_html=True)
        left, right = st.columns([1.25, 1], gap="large")
        with left:
            st.markdown('<div class="column-heading"><b>Ask the archive</b></div>', unsafe_allow_html=True)
            with st.form("question_form"):
                st.text_area("Question", key="question", height=160, placeholder="Enter your question…", max_chars=1500, disabled=active, label_visibility="collapsed")
                submit = st.form_submit_button("Start research →", type="primary", disabled=active, use_container_width=True)
                st.caption("Each question is independent. Use launch scope above to narrow your research.")
            if submit:
                question = st.session_state.question.strip()
                if not question:
                    st.warning("Enter a question to start your research.")
                else:
                    settings = Settings.from_env()
                    if settings.missing_for("typesafe_api_key", "nebius_api_key", "nebius_model"):
                        st.error("The research service is not configured yet. Please contact your administrator.")
                    else:
                        trace = RunTrace("research-ui")
                        st.session_state.job = {"trace": trace, "future": workers().submit(execute, question, trace, archive, scope), "started": perf_counter()}
                        st.session_state.pop("current", None)
                        st.session_state.scroll_to_research = True
                        st.rerun()
            current = st.session_state.get("current")
            if active:
                _, label = activity(events)
                st.markdown('<div class="research-status" role="status"><span class="status-dot"></span>' + escape(label) + '</div>', unsafe_allow_html=True)
                if perf_counter() - job["started"] > 60:
                    st.info("Your research is taking longer than usual. It is still in progress.")
            elif current:
                result = current["result"]
                status = result.get("status", "error")
                labels = {"answered": "Research complete", "blocked": "Outside the archive’s scope", "insufficient_evidence": "More information is needed", "error": "Research unavailable", "not_configured": "Research unavailable"}
                answer = result.get("answer") or result.get("message") or "No answer was returned."
                if status in {"not_configured", "error"}:
                    answer = "We couldn’t complete your research. Please try again shortly. If the problem continues, contact your administrator."
                with st.container(border=True, key="answer_panel"):
                    st.markdown('<div class="answer-label">' + escape(labels.get(status, "Research result").upper()) + '</div>', unsafe_allow_html=True)
                    if current.get("scope", "All launches") != "All launches":
                        st.caption("Launch scope: " + current["scope"])
                    if status == "answered":
                        st.markdown(display_answer(answer))
                    elif status == "blocked":
                        st.warning(answer)
                    else:
                        st.info(answer)
            else:
                st.markdown('<div class="answer-placeholder"><span>02 / YOUR FINDINGS</span><h3>Your answer will appear here.</h3><p>Start with a question about an incident, a revised finding or a corrective action.</p></div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="column-heading"><span>RESEARCH JOURNEY</span><b>From information to insight</b></div>', unsafe_allow_html=True)
            current = st.session_state.get("current")
            visual_state = "working" if active else "complete" if current and current["result"].get("status") == "answered" else "stopped" if current else "idle"
            st.iframe(launch_html(visual_state), height=600)
        # Scroll once after submission, not on the periodic progress updates.
        if st.session_state.pop("scroll_to_research", False):
            components.html("""<script>
                setTimeout(() => {
                    const target = window.parent.document.getElementById('research-workspace');
                    if (target) target.scrollIntoView({behavior: 'smooth', block: 'start'});
                }, 250);
            </script>""", height=0, width=0)
    workspace()
    footer()


# A native full-screen button keeps click and keyboard entry in Streamlit state.
if not st.session_state.get("entered", False):
    st.markdown(entrance_html(), unsafe_allow_html=True)
    if st.button("Enter Launch-Deets", key="enter_space"):
        st.session_state.entered = True
        st.rerun()
    st.stop()

# Native pages preserve distinct Home and Research URLs; no conversation history is retained.
st.session_state.pop("history", None)
home_page = st.Page(home, title="Home", default=True)
research_page = st.Page(research, title="Research", url_path="research")
page = st.navigation([home_page, research_page], position="hidden")
brand, navigation = st.columns([3, 2], vertical_alignment="center")
with brand:
    st.markdown('<div class="wordmark"><span class="brand-icon">↗</span> launch-deets<span class="wordmark-sub">LAUNCH RESEARCH</span></div>', unsafe_allow_html=True)
with navigation:
    with st.container(horizontal=True, horizontal_alignment="right", gap="small", key="primary_navigation"):
        st.page_link(home_page, label="Home", disabled="job" in st.session_state, width="content")
        st.page_link(research_page, label="Research", disabled="job" in st.session_state, width="content")
st.markdown('<div class="nav-rule"></div>', unsafe_allow_html=True)
page.run()
