"""
app.py
------
WhatsApp Chat Analyzer - a professional Streamlit analytics dashboard.

Run locally with:   streamlit run app.py
Deploy on:           Streamlit Community Cloud (see requirements.txt)
"""

import io
import traceback

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

import preprocessor
import helper

# ===========================================================================
# PAGE CONFIG
# ===========================================================================

st.set_page_config(
    page_title="WhatsApp Chat Analyzer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "A professional analytics dashboard for WhatsApp chat exports, "
                  "built with Streamlit, Plotly, and Python."
    },
)

# ===========================================================================
# CUSTOM CSS - modern cards, shadows, hover effects
# ===========================================================================

st.markdown("""
<style>
    /* ---- General ---- */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1, h2, h3, h4 { font-family: 'Segoe UI', 'Trebuchet MS', sans-serif; }

    /* ---- Metric cards ---- */
    .metric-card {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        padding: 24px 18px;
        border-radius: 18px;
        text-align: center;
        color: white;
        box-shadow: 0 6px 18px rgba(18, 140, 126, 0.35);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 24px rgba(18, 140, 126, 0.5);
    }
    .metric-card p {
        font-size: 0.82rem;
        margin: 0;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }
    .metric-card h1 {
        font-size: 2.2rem;
        margin: 6px 0 0 0;
        font-weight: 800;
    }

    /* ---- Secondary metric card (neutral) ---- */
    .metric-card-alt {
        background: #1c1f26;
        border: 1px solid #2b2f3a;
        padding: 22px 18px;
        border-radius: 18px;
        text-align: center;
        color: #e5e7eb;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    .metric-card-alt:hover {
        transform: translateY(-4px);
        border-color: #25D366;
    }
    .metric-card-alt p {
        font-size: 0.8rem; margin: 0; opacity: 0.7;
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .metric-card-alt h2 {
        font-size: 1.7rem; margin: 6px 0 0 0; color: #25D366;
    }

    /* ---- Insight / info cards ---- */
    .insight-card {
        background: #1c1f26;
        border: 1px solid #2b2f3a;
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.2);
        transition: box-shadow 0.2s ease;
    }
    .insight-card:hover { box-shadow: 0 8px 20px rgba(0,0,0,0.35); }
    .insight-card h3 { margin-top: 0; color: #25D366; font-size: 1.0rem; }

    /* ---- Section header ---- */
    .section-header {
        border-left: 5px solid #25D366;
        padding-left: 14px;
        margin: 8px 0 18px 0;
    }
    .section-header h2 { margin: 0; }
    .section-header p { margin: 2px 0 0 0; opacity: 0.65; font-size: 0.9rem; }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] { background-color: #12151c; }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1c1f26;
        border-radius: 10px 10px 0 0;
        padding: 10px 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background-color: #128C7E !important; }

    /* ---- Dataframes / containers ---- */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ---- Footer ---- */
    .footer {
        text-align: center;
        padding: 18px 0 4px 0;
        opacity: 0.6;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# REUSABLE UI HELPERS
# ===========================================================================

def metric_card(label: str, value):
    st.markdown(f"""
        <div class="metric-card">
            <p>{label}</p>
            <h1>{value}</h1>
        </div>
    """, unsafe_allow_html=True)


def metric_card_alt(label: str, value):
    st.markdown(f"""
        <div class="metric-card-alt">
            <p>{label}</p>
            <h2>{value}</h2>
        </div>
    """, unsafe_allow_html=True)


def insight_card(title: str, body_html: str):
    st.markdown(f"""
        <div class="insight-card">
            <h3>{title}</h3>
            {body_html}
        </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
        <div class="section-header">
            <h2>{title}</h2>
            <p>{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes) -> pd.DataFrame:
    """Decode + preprocess the uploaded file. Cached so re-runs are instant."""
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("utf-8", errors="ignore")
    return preprocessor.preprocess(text)


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


# ===========================================================================
# SIDEBAR
# ===========================================================================

with st.sidebar:
    st.markdown("## 💬 WhatsApp Chat Analyzer")
    st.caption("Professional analytics dashboard for your chat exports.")
    st.markdown("---")

    uploaded_file = st.file_uploader("📁 Upload WhatsApp chat (.txt)", type=["txt"])

    st.markdown("---")
    st.caption(
        "**How to export:** Open a chat in WhatsApp → ⋮ Menu → More → "
        "Export chat → **Without Media** → save/share the `.txt` file."
    )

# ---- Landing state: no file uploaded yet ----
if uploaded_file is None:
    st.title("💬 WhatsApp Chat Analyzer")
    st.info("👈 Upload a WhatsApp `.txt` export from the sidebar to begin.")

    section_header("About This Project", "What you'll get once you upload a chat")
    st.markdown("""
    This dashboard turns a raw WhatsApp chat export into a full analytics report:

    - **📊 Overall Statistics** — total messages, words, media, and links
    - **👥 User Analysis** — most active users and their % contribution
    - **📅 Timeline Analysis** — monthly and daily message trends
    - **🔥 Activity Analysis** — weekly, monthly, hourly activity + heatmap
    - **☁️ Text Analysis** — word cloud and most common words
    - **😀 Emoji Analysis** — emoji frequency table and chart
    - **🔗 Link Analysis** — shared link counts and top domains
    - **🖼️ Media Analysis** — breakdown of images, videos, audio, stickers, documents
    - **🧠 Advanced Analytics** — response times, chat streaks, sentiment,
      message length distribution, busiest hour, weekday vs weekend split

    All processing happens **locally in this session** — your chat data is never
    stored or sent anywhere else.
    """)
    st.stop()

# ---- Parse the uploaded file ----
try:
    with st.spinner("🔄 Preprocessing chat data..."):
        df = load_data(uploaded_file.getvalue())
except Exception as e:
    st.error(f"❌ Couldn't parse this file: {e}")
    with st.expander("Show technical details"):
        st.code(traceback.format_exc())
    st.stop()

if df.empty:
    st.error("⚠️ No messages could be parsed from this file. "
              "Please check that it's a valid WhatsApp export.")
    st.stop()

st.sidebar.success(f"✅ Parsed {df.shape[0]:,} messages successfully!")

# ---- User selector + Analyze button ----
user_list = sorted([u for u in df['user'].unique() if u != 'Group Notification'])
user_list.insert(0, "Overall")

with st.sidebar:
    selected_user = st.selectbox("👤 Analyze for", user_list)
    analyze_clicked = st.button("🔍 Analyze", use_container_width=True, type="primary")

    st.markdown("---")
    st.caption(f"**{df.shape[0]:,}** total lines · **{len(user_list) - 1}** participants")

    st.markdown("---")
    csv_bytes = dataframe_to_csv_bytes(df.drop(columns=['period'], errors='ignore'))
    st.download_button(
        "⬇️ Download Cleaned Dataset (CSV)",
        data=csv_bytes,
        file_name="whatsapp_chat_cleaned.csv",
        mime="text/csv",
        use_container_width=True,
    )

if not analyze_clicked:
    st.title("💬 WhatsApp Chat Analyzer")
    st.success("File loaded! Choose a user (or keep **Overall**) and click **🔍 Analyze**.")
    st.dataframe(df[['date', 'user', 'message']].head(10), use_container_width=True, hide_index=True)
    st.stop()

# ===========================================================================
# MAIN DASHBOARD
# ===========================================================================

st.title("💬 WhatsApp Chat Analyzer")
st.markdown(f"#### Showing analysis for: `{selected_user}`")

tabs = st.tabs([
    "📊 Overview", "👥 Users", "📅 Timeline", "🔥 Activity",
    "☁️ Text", "😀 Emoji", "🔗 Links", "🖼️ Media",
    "🧠 Advanced", "ℹ️ About"
])

# ---------------------------------------------------------------------------
# TAB: Overview - Overall Statistics
# ---------------------------------------------------------------------------
with tabs[0]:
    section_header("Overall Statistics", "High-level snapshot of the conversation")

    try:
        num_messages, num_words, num_media, num_links = helper.fetch_stats(selected_user, df)

        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("Total Messages", f"{num_messages:,}")
        with c2: metric_card("Total Words", f"{num_words:,}")
        with c3: metric_card("Media Messages", f"{num_media:,}")
        with c4: metric_card("Links Shared", f"{num_links:,}")
    except Exception as e:
        st.error(f"Could not compute overall statistics: {e}")

# ---------------------------------------------------------------------------
# TAB: Users - Most Active, % contribution, bar chart
# ---------------------------------------------------------------------------
with tabs[1]:
    section_header("User Analysis", "Who drives the conversation")

    if selected_user != "Overall":
        st.info("Switch to **Overall** in the sidebar to compare all users.")
    else:
        try:
            busy_counts, busy_pct = helper.most_busy_users(df)

            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown("**🏆 Top Active Users**")
                fig = px.bar(
                    x=busy_counts.index, y=busy_counts.values,
                    labels={'x': 'User', 'y': 'Messages'},
                    color=busy_counts.values, color_continuous_scale='Greens',
                )
                fig.update_layout(showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("**📈 Contribution %**")
                st.dataframe(busy_pct.head(10), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Could not compute user analysis: {e}")

# ---------------------------------------------------------------------------
# TAB: Timeline - Monthly & Daily
# ---------------------------------------------------------------------------
with tabs[2]:
    section_header("Timeline Analysis", "Message volume trends over time")

    try:
        st.markdown("**📈 Monthly Timeline**")
        timeline = helper.monthly_timeline(selected_user, df)
        fig = px.line(timeline, x='time', y='message', markers=True,
                      labels={'time': 'Month', 'message': 'Messages'})
        fig.update_traces(line_color='#25D366', marker=dict(size=7))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**📉 Daily Timeline**")
        daily = helper.daily_timeline(selected_user, df)
        fig = px.line(daily, x='only_date', y='message',
                      labels={'only_date': 'Date', 'message': 'Messages'})
        fig.update_traces(line_color='#128C7E')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not compute timeline analysis: {e}")

# ---------------------------------------------------------------------------
# TAB: Activity - Weekly, Monthly, Hourly, Heatmap
# ---------------------------------------------------------------------------
with tabs[3]:
    section_header("Activity Analysis", "When the conversation is most active")

    try:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📆 Weekly Activity**")
            week_activity = helper.week_activity_map(selected_user, df)
            fig = px.bar(x=week_activity.index, y=week_activity.values,
                         labels={'x': 'Day', 'y': 'Messages'},
                         color=week_activity.values, color_continuous_scale='Teal')
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**🗓️ Monthly Activity**")
            month_activity = helper.month_activity_map(selected_user, df)
            fig = px.bar(x=month_activity.index, y=month_activity.values,
                         labels={'x': 'Month', 'y': 'Messages'},
                         color=month_activity.values, color_continuous_scale='Oranges')
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("**🕐 Hourly Activity**")
        hourly = helper.hourly_activity_map(selected_user, df)
        fig = px.line(x=hourly.index, y=hourly.values, markers=True,
                      labels={'x': 'Hour of Day', 'y': 'Messages'})
        fig.update_traces(line_color='#25D366')
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**🔥 Weekly Activity Heatmap**")
        heatmap = helper.activity_heatmap(selected_user, df)
        fig = go.Figure(data=go.Heatmap(
            z=heatmap.values, x=heatmap.columns, y=heatmap.index, colorscale='Greens'
        ))
        fig.update_layout(xaxis_title="Time Period (hour)", yaxis_title="Day", height=450)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not compute activity analysis: {e}")

# ---------------------------------------------------------------------------
# TAB: Text - Word Cloud & Common Words
# ---------------------------------------------------------------------------
with tabs[4]:
    section_header("Text Analysis", "What's being talked about")

    try:
        st.markdown("**☁️ Word Cloud**")
        wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.imshow(wc)
        ax.axis('off')
        fig.patch.set_alpha(0.0)
        st.pyplot(fig)

        st.markdown("**🔠 Top 20 Most Common Words**")
        common_df = helper.most_common_words(selected_user, df)
        if not common_df.empty:
            fig = px.bar(common_df.sort_values('count'), x='count', y='word',
                         orientation='h', color='count', color_continuous_scale='Greens')
            fig.update_layout(showlegend=False, coloraxis_showscale=False, height=550,
                               yaxis_title="", xaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough text data to compute common words.")
    except Exception as e:
        st.error(f"Could not compute text analysis: {e}")

# ---------------------------------------------------------------------------
# TAB: Emoji
# ---------------------------------------------------------------------------
with tabs[5]:
    section_header("Emoji Analysis", "Most used emojis in the chat")

    try:
        emoji_df = helper.emoji_helper(selected_user, df)
        if emoji_df.empty:
            st.info("No emojis found for this selection.")
        else:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("**📋 Emoji Frequency Table**")
                st.dataframe(emoji_df.head(20), use_container_width=True, hide_index=True)
            with col2:
                st.markdown("**📊 Emoji Bar Chart**")
                fig = px.bar(emoji_df.head(10), x='emoji', y='count',
                             color='count', color_continuous_scale='Greens')
                fig.update_layout(showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not compute emoji analysis: {e}")

# ---------------------------------------------------------------------------
# TAB: Links
# ---------------------------------------------------------------------------
with tabs[6]:
    section_header("Link Analysis", "Shared links and their sources")

    try:
        links_df = helper.extract_links(selected_user, df)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**🔗 Shared Links** ({len(links_df)} unique)")
            if links_df.empty:
                st.info("No links were shared in this selection.")
            else:
                st.dataframe(links_df, use_container_width=True, hide_index=True,
                             column_config={"Link": st.column_config.LinkColumn("Link")})

        with col2:
            st.markdown("**🌐 Top Shared Domains**")
            domains_df = helper.top_domains(selected_user, df)
            if domains_df.empty:
                st.info("No domains to display.")
            else:
                fig = px.bar(domains_df.sort_values('Count'), x='Count', y='Domain',
                             orientation='h', color='Count', color_continuous_scale='Blues')
                fig.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not compute link analysis: {e}")

# ---------------------------------------------------------------------------
# TAB: Media - Images, Videos, Audio, Stickers, Documents
# ---------------------------------------------------------------------------
with tabs[7]:
    section_header("Media Analysis", "Breakdown of shared media types")

    try:
        media_counts = helper.media_breakdown(selected_user, df)
        if media_counts.empty:
            st.info("No media messages found for this selection.")
        else:
            cols = st.columns(len(media_counts))
            icons = {"Image": "🖼️", "Video": "🎥", "Audio": "🎵",
                     "Sticker": "🌟", "Document": "📄", "GIF": "🎞️"}
            for col, (media_type, count) in zip(cols, media_counts.items()):
                with col:
                    metric_card_alt(f"{icons.get(media_type, '📦')} {media_type}", f"{count:,}")

            st.markdown("<br>", unsafe_allow_html=True)
            fig = px.pie(values=media_counts.values, names=media_counts.index,
                         title="Media Type Distribution", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Greens_r)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not compute media analysis: {e}")

# ---------------------------------------------------------------------------
# TAB: Advanced Analytics
# ---------------------------------------------------------------------------
with tabs[8]:
    section_header("Advanced Analytics", "Deeper behavioral insights")

    try:
        # --- Response time & streaks ---
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**⏱️ Average Response Time by User** (minutes)")
            avg_resp, _ = helper.response_time_analysis(df)
            if not avg_resp.empty:
                top_resp = avg_resp.head(10).reset_index()
                top_resp.columns = ['User', 'Avg Response Time (min)']
                top_resp['Avg Response Time (min)'] = top_resp['Avg Response Time (min)'].round(1)
                fig = px.bar(top_resp, x='User', y='Avg Response Time (min)',
                             color='Avg Response Time (min)', color_continuous_scale='RdYlGn_r')
                fig.update_layout(showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to compute response times.")

        with col2:
            st.markdown("**🔥 Chat Streaks**")
            streaks = helper.chat_streaks(df)
            insight_card("Longest Active Streak",
                          f"<p style='font-size:1.6rem;margin:0;'><b>{streaks['longest_streak']} days</b></p>"
                          f"<p style='opacity:0.7;'>{streaks['streak_start']} → {streaks['streak_end']}</p>")
            insight_card("Longest Inactive Gap",
                          f"<p style='font-size:1.6rem;margin:0;'><b>{streaks['longest_gap']} days</b></p>")
            insight_card("Current Streak",
                          f"<p style='font-size:1.6rem;margin:0;'><b>{streaks['current_streak']} days</b></p>")

        st.markdown("---")

        # --- Weekday vs Weekend + Busiest hour ---
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📅 Weekend vs Weekday**")
            wv = helper.weekend_vs_weekday(selected_user, df)
            fig = px.pie(values=wv.values, names=wv.index, hole=0.4,
                         color=wv.index,
                         color_discrete_map={'Weekday': '#128C7E', 'Weekend': '#25D366'})
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**🕐 Most Active Hour**")
            hourly = helper.hourly_activity_map(selected_user, df)
            if not hourly.empty:
                busiest = hourly.idxmax()
                metric_card_alt("Peak Hour", f"{busiest:02d}:00 – {(busiest + 1) % 24:02d}:00")
                st.markdown("<br>", unsafe_allow_html=True)
                fig = px.bar(x=hourly.index, y=hourly.values,
                             labels={'x': 'Hour', 'y': 'Messages'},
                             color=hourly.values, color_continuous_scale='Viridis')
                fig.update_layout(showlegend=False, coloraxis_showscale=False)
                fig.update_xaxes(dtick=1)
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # --- Message length distribution ---
        st.markdown("**📏 Message Length Distribution**")
        lengths = helper.message_length_distribution(selected_user, df)
        if not lengths.empty:
            fig = px.histogram(lengths, nbins=40, labels={'value': 'Message Length (characters)'},
                                color_discrete_sequence=['#25D366'])
            fig.update_layout(showlegend=False, yaxis_title="Frequency")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough text data for a length distribution.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📝 Longest Messages**")
            st.dataframe(helper.longest_messages(selected_user, df),
                         use_container_width=True, hide_index=True)
        with col2:
            st.markdown("**📊 Avg. Message Length by User**")
            st.dataframe(helper.avg_message_length_by_user(df),
                         use_container_width=True)

        st.markdown("---")

        # --- Sentiment ---
        st.markdown("**💭 Sentiment Analysis**")
        sent_df, sent_summary, sent_by_user = helper.sentiment_analysis(selected_user, df)
        if sent_summary.empty:
            st.info("Not enough text to analyze sentiment.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                colors = {'Positive': '#25D366', 'Neutral': '#94a3b8', 'Negative': '#ef4444'}
                fig = px.pie(values=sent_summary.values, names=sent_summary.index,
                             color=sent_summary.index, color_discrete_map=colors,
                             title="Message Sentiment Distribution", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                if selected_user == "Overall" and len(sent_by_user) > 1:
                    top_pos = sent_by_user.head(5).reset_index()
                    top_pos.columns = ['User', 'Avg Sentiment Score']
                    fig = px.bar(top_pos, x='User', y='Avg Sentiment Score',
                                 color='Avg Sentiment Score', color_continuous_scale='RdYlGn',
                                 title="Most Positive Users (avg. sentiment)")
                    fig.update_layout(showlegend=False, coloraxis_showscale=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    avg_score = sent_df['sentiment_score'].mean()
                    mood = ("😊 Positive" if avg_score >= 0.05
                            else "☹️ Negative" if avg_score <= -0.05 else "😐 Neutral")
                    metric_card_alt("Overall Mood", mood)

    except Exception as e:
        st.error(f"Could not compute advanced analytics: {e}")
        with st.expander("Show technical details"):
            st.code(traceback.format_exc())

# ---------------------------------------------------------------------------
# TAB: About
# ---------------------------------------------------------------------------
with tabs[9]:
    section_header("About This Project", "What's under the hood")
    st.markdown("""
    **WhatsApp Chat Analyzer** is a professional analytics dashboard that turns a
    raw WhatsApp `.txt` chat export into rich, interactive insights.

    #### 🧩 Architecture
    - `preprocessor.py` — parses the raw export into a structured pandas DataFrame,
      auto-detecting Android/iOS date formats and classifying media types.
    - `helper.py` — pure analysis functions (statistics, timelines, activity,
      text/emoji/link analysis, sentiment, streaks, response time).
    - `app.py` — the Streamlit UI layer: layout, styling, charts, and error handling.

    #### 📈 Features
    - Overall statistics: messages, words, media, links
    - User analysis: most active users, % contribution
    - Timeline analysis: monthly & daily trends
    - Activity analysis: weekly / monthly / hourly activity + heatmap
    - Text analysis: word cloud, top 20 common words
    - Emoji analysis: frequency table & chart
    - Link analysis: shared links, top domains
    - Media analysis: images, video, audio, stickers, documents
    - Advanced analytics: response time, chat streaks, sentiment, message length
      distribution, busiest hour, weekend vs weekday split
    - CSV export of the cleaned dataset

    #### 🔒 Privacy
    All parsing and analysis happens **locally in your browser session**.
    No chat data is stored, logged, or transmitted elsewhere.

    #### 🛠️ Built with
    Streamlit · Pandas · Plotly · Matplotlib · WordCloud · VADER Sentiment
    """)

# ===========================================================================
# FOOTER
# ===========================================================================
st.markdown("""
    <div class="footer">
        Built with ❤️ using Streamlit · WhatsApp Chat Analyzer &copy; 2026
    </div>
""", unsafe_allow_html=True)