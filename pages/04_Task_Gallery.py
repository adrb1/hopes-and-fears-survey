import streamlit as st

from survey_app.shared import (
    bootstrap_page,
    components,
    get_tasks_gallery_for_ui,
    go_to_page,
    queue_task_event,
    render_view_anchor,
)


anchor_id = bootstrap_page(4)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='text-align: center; margin-bottom: 40px;'>
        <div style='display: flex; justify-content: center; align-items: center; gap: 28px; flex-wrap: wrap; margin-bottom: 8px;'>
            <h2 style='margin: 0; font-weight: bold; letter-spacing: 2px; color: #E63946;'>WHOSE FEARS?</h2>
            <h2 style='margin: 0; font-weight: bold; letter-spacing: 2px; color: #43AA8B;'>WHOSE HOPES?</h2>
        </div>
        <h1 style='font-size: 28px; font-weight: bold; margin-top: 20px;'>TASK AUTOMATION GALLERY</h1>
        <p style='color: #666; margin-top: 10px;'>Click and read about your job automation potential</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tasks_gallery = get_tasks_gallery_for_ui()

if st.session_state.selected_task is not None:
    if st.session_state.last_detail_scroll_token != st.session_state.detail_open_token:
        st.session_state.last_detail_scroll_token = st.session_state.detail_open_token
        components.html(
            """
            <script>
                (function () {
                    const w = window.parent;
                    const doc = w.document;
                    function jumpToDetailTop() {
                        const detailTop = doc.getElementById("hf-task-detail-top");
                        if (detailTop) {
                            detailTop.scrollIntoView({ block: "start", inline: "nearest", behavior: "auto" });
                            return;
                        }
                        const main = doc.querySelector("[data-testid='stAppViewContainer'] > .main");
                        w.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                        if (main) main.scrollTop = 0;
                    }

                    jumpToDetailTop();
                    let count = 0;
                    const timer = setInterval(() => {
                        jumpToDetailTop();
                        count += 1;
                        if (count >= 6) clearInterval(timer);
                    }, 40);
                })();
            </script>
            """,
            height=0,
        )

    task = next((item for item in tasks_gallery if item["id"] == st.session_state.selected_task), None)
    if task:
        header_color = "#E63946" if task["risk_level"] == "HIGH" else "#F4A000" if task["risk_level"] == "MEDIUM" else "#43AA8B"
        _, center_col, _ = st.columns([0.05, 0.9, 0.05])
        with center_col:
            st.markdown("<div id='hf-task-detail-top' style='height:1px; margin:0; padding:0; scroll-margin-top:72px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style='background: {header_color}; color: white; padding: 25px 30px; border-radius: 8px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;'>
                    <h2 style='margin: 0; font-size: 20px; font-weight: 700;'>{task['title']}</h2>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_close1, col_close2 = st.columns([0.9, 0.1])
            with col_close2:
                if st.button("✕", key="close_modal"):
                    queue_task_event(task["id"], "close")
                    st.session_state.selected_task = None
                    st.rerun()

            color = "#E63946" if task["risk_level"] == "HIGH" else "#F4D35E" if task["risk_level"] == "MEDIUM" else "#43AA8B"
            risk_text = f"{task['risk_level']} RISK"
            st.markdown(
                f"""
                <div style='background: {color}; color: white; padding: 8px 12px; border-radius: 4px; display: inline-block; margin: 10px 0;'>
                    <strong>{risk_text}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f"**AI AGENT CAPABILITY:** {task['capability']}")
            st.markdown(f"**EXAMPLE TECHNOLOGY:** {task['example_tech']}")
            st.markdown("**RISK ANALYSIS:**")
            st.markdown(task["risk_analysis"])
            st.markdown("**Task Dimensions:**")
            dimensions_emojis = {"Mental": "🧠", "Individual": "👤", "Routine": "📋", "Easy": "😊"}
            cols = st.columns(len(task["dimensions"]))
            for idx, dim in enumerate(task["dimensions"]):
                with cols[idx]:
                    st.markdown(f"{dimensions_emojis.get(dim, '')} {dim}")
            if st.button("More →", key=f"task_more_{task['id']}"):
                queue_task_event(task["id"], "open_more")
                st.session_state.selected_task = None
                st.rerun()
else:
    st.session_state.last_scrolled_task_id = None

st.markdown("---")
risk_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
ordered_tasks = sorted(tasks_gallery, key=lambda item: (risk_rank.get(item.get("risk_level"), 1), item.get("id", 0)))
n_cols = 5
n_rows = max(1, (len(ordered_tasks) + n_cols - 1) // n_cols)
columns_tasks = [[None for _ in range(n_rows)] for _ in range(n_cols)]

for index, task in enumerate(ordered_tasks):
    col_i = index // n_rows
    pos_in_col = index % n_rows
    if col_i >= n_cols:
        break
    row_i = pos_in_col if col_i % 2 == 0 else n_rows - 1 - pos_in_col
    columns_tasks[col_i][row_i] = task


def risk_color(level):
    if level == "HIGH":
        return "#E63946"
    if level == "MEDIUM":
        return "#F4A000"
    return "#43AA8B"


st.markdown(
    """
    <style>
    .task-card-wrapper {
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    .task-card {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
    }
    .task-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .risk-gradient-hint {
        margin: 0 0 14px 0;
        padding: 8px 12px;
        border-radius: 8px;
        background: linear-gradient(90deg, #E63946 0%, #F4A000 50%, #43AA8B 100%);
        color: #fff;
        font-weight: 700;
        text-align: center;
        letter-spacing: 0.2px;
        font-size: 12px;
    }
    .stButton > button {
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 6px;
        transition: all 0.2s ease;
        width: 100%;
        font-size: 14px;
        white-space: nowrap;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='risk-gradient-hint'>RED → GREEN (serpentine layout)</div>", unsafe_allow_html=True)


def render_task_cell(task):
    color = risk_color(task.get("risk_level"))
    risk_text = task.get("risk_level", "MEDIUM")
    st.markdown(
        f"""
        <div class='task-card-wrapper'>
            <div class='task-card' style='background: linear-gradient(135deg, {color} 0%, {color} 100%);
                 color: white; padding: 18px; border-radius: 8px; min-height: 98px;
                 display: flex; align-items: center; justify-content: center; text-align: center;'>
                <div style='font-weight: 700; font-size: 13px; line-height: 1.3;'>
                    {task['title']}<br>
                    <span style='font-size: 11px; opacity: 0.9;'>[{risk_text}]</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(label="📖 View Details", key=f"task_{task['id']}", use_container_width=True):
        st.session_state.selected_task = task["id"]
        st.session_state.detail_open_token += 1
        st.session_state.viewed_task_ids.add(task["id"])
        queue_task_event(task["id"], "view")
        st.rerun()


cols5 = st.columns(n_cols, gap="small")
for col_i in range(n_cols):
    with cols5[col_i]:
        for task in columns_tasks[col_i]:
            if task is not None:
                render_task_cell(task)

st.markdown("---")
MIN_VIEWS = 5
viewed_count = len(st.session_state.viewed_task_ids)
col_prev, _, col_next = st.columns([0.2, 0.65, 0.15])
with col_prev:
    if st.button("← Previous", key="page4_prev"):
        go_to_page(3)
with col_next:
    if viewed_count < MIN_VIEWS:
        st.button("Next →", key="page4_next", disabled=True)
        st.caption(f"Please view at least {MIN_VIEWS} task details to continue ({viewed_count}/{MIN_VIEWS} viewed).")
    else:
        if st.button("Next →", key="page4_next"):
            go_to_page(5)
