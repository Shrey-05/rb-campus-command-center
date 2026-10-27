"""
app.py
======
WHAT THIS FILE IS (plain English):

This is the actual dashboard you see in your browser. It never touches the
raw Excel files - it only reads the clean CSVs that clean_data.py produced
in data/clean/.

The app is organized as a sidebar with one page per "feature." Right now
only Feature 1 (Overview Dashboard) is built. We'll add more pages one at a
time.

HOW TO RUN THIS:
    streamlit run app.py

Then your browser should open automatically to something like
http://localhost:8501
"""

import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# PAGE SETUP - runs once, sets the browser tab title and layout
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Red Bull Campus Activation Command Center",
    page_icon="⚡",
    layout="wide",
)

CLEAN_DIR = "data/clean"

# ---------------------------------------------------------------------------
# PALETTE - adopted as-is from the "dark-mode" theme
# (github.com/jmedia65/awesome-streamlit-themes). Background, sidebar,
# borders, radius, and fonts are all handled natively by
# .streamlit/config.toml - these Python constants just mirror those same
# values for the few custom bits config.toml can't do (the page header
# banner, the sidebar brand mark, and chart colors).
BRAND_BG = "#0d1117"
BRAND_SURFACE = "#161b22"
BRAND_SURFACE_2 = "#21262d"
BRAND_ACCENT = "#a855f7"       # purple - the theme's one primary accent
BRAND_LINK = "#58a6ff"         # blue - secondary emphasis, matches linkColor
BRAND_TEXT = "#f0f6fc"
BRAND_TEXT_MUTED = "#8b949e"
BRAND_BORDER = "#30363d"

# Status colors used consistently everywhere in the app - kept as their own
# distinct set (independent of the purple accent) so a "Needs Follow-Up"
# table cell always reads as a status, never as brand chrome.
STATUS_COLORS = {
    "On Track": "#3fb950",          # green
    "At Risk": "#d29922",           # amber
    "Needs Follow-Up": "#f85149",   # red
    "Incomplete Data": "#6e7681",   # slate grey - see explanation below
}

REQUIRED_FIELDS = ["owner_sm_name", "integration_plan", "assets_required", "asset_qty", "budget"]



# ---------------------------------------------------------------------------
# CUSTOM STYLING (plain English: this one CSS block is what gives the whole
# app its remaining custom touches - the page header banner, sidebar brand
# mark, and active-nav highlight. Everything else (background, sidebar,
# borders, radius, fonts) now comes from .streamlit/config.toml natively,
# which is more robust across Streamlit versions than CSS overrides.)
# ---------------------------------------------------------------------------
CUSTOM_CSS = f"""
<style>
:root {{
    --rb-accent: {BRAND_ACCENT};
    --rb-link: {BRAND_LINK};
    --rb-text-muted: {BRAND_TEXT_MUTED};
    --rb-border: {BRAND_BORDER};
}}

/* a little breathing room around the main content */
[data-testid="stAppViewContainer"] .block-container {{
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}}

/* active sidebar nav item gets a quiet accent bar - a structural signal
   for "this is where you are," not decoration */
[data-testid="stSidebar"] label:has(input:checked) {{
    background: rgba(168, 85, 247, 0.12);
    border-left: 2px solid var(--rb-accent);
    border-radius: 4px;
}}
[data-testid="stSidebar"] label {{
    padding: 7px 10px;
    border-left: 2px solid transparent;
    margin-bottom: 1px;
    font-size: 0.92rem;
}}

/* the branded page header block (see render_header() below) */
.rb-header {{
    border-left: 3px solid var(--rb-accent);
    padding: 2px 0 2px 16px;
    margin-bottom: 1.4em;
}}
.rb-header .rb-title {{
    font-weight: 700;
    font-size: 1.9rem;
    line-height: 1.15;
    margin: 0;
}}
.rb-header .rb-subtitle {{
    color: var(--rb-text-muted);
    font-size: 0.92rem;
    margin-top: 3px;
}}

/* sidebar brand lockup at the top - a flat, simple monogram */
.rb-sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 2px 0 16px 0;
    border-bottom: 1px solid var(--rb-border);
    margin-bottom: 14px;
}}
.rb-sidebar-brand .rb-mark {{
    width: 32px;
    height: 32px;
    border-radius: 6px;
    background: rgba(168, 85, 247, 0.12);
    border: 1px solid rgba(168, 85, 247, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
    color: var(--rb-accent);
    flex-shrink: 0;
}}
.rb-sidebar-brand .rb-brand-text {{
    font-weight: 700;
    font-size: 1rem;
    line-height: 1.15;
}}
.rb-sidebar-brand .rb-brand-sub {{
    color: var(--rb-text-muted);
    font-size: 0.72rem;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header(title, subtitle):
    """
    Plain English: this replaces the plain st.title()/st.caption() pair with
    a branded header block (a quiet accent bar + condensed headline). Used
    at the top of every page so the look is consistent everywhere.
    """
    st.markdown(
        f"""
        <div class="rb-header">
            <p class="rb-title">{title}</p>
            <p class="rb-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_chart(fig):
    """
    Plain English: applies the same dark, branded look to every Plotly
    chart in the app, so charts don't show up with a mismatched white
    background against the rest of the dark UI.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BRAND_SURFACE,
        plot_bgcolor=BRAND_SURFACE,
        font=dict(family="Inter, sans-serif", color=BRAND_TEXT),
        title_font=dict(family="Inter, sans-serif", size=18, color=BRAND_TEXT),
        margin=dict(t=50, l=10, r=10, b=10),
    )
    fig.update_xaxes(gridcolor=BRAND_SURFACE_2)
    fig.update_yaxes(gridcolor=BRAND_SURFACE_2)
    return fig


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------
# @st.cache_data means: only actually re-read the CSV from disk once, then
# reuse it in memory - makes the app feel instant when you click around.
@st.cache_data
def load_activations():
    df = pd.read_csv(f"{CLEAN_DIR}/activations_clean.csv")
    df["activation_date"] = pd.to_datetime(df["activation_date"], errors="coerce").dt.date
    return df


@st.cache_data
def load_events():
    return pd.read_csv(f"{CLEAN_DIR}/events_3p_clean.csv")


@st.cache_data
def load_fest_tracker():
    return pd.read_csv(f"{CLEAN_DIR}/fest_tracker_clean.csv")


# ---------------------------------------------------------------------------
# FEATURE 1 LOGIC: compute a status for each activation row
# ---------------------------------------------------------------------------
def compute_status(row, today):
    """
    Returns one of: "On Track", "At Risk", "Needs Follow-Up", "Incomplete Data"

    This follows the rules from the project spec:
      - On Track: activation date is in the future, no missing required fields
      - At Risk: activation date is within 5 days AND assets/budget still blank
      - Needs Follow-Up: activation date has passed with no completion note
        (this dataset has no "completion note" column, so any past activation
        is treated as needing follow-up)
      - Incomplete Data: doesn't cleanly fit the three rules above - e.g. no
        usable date, or a far-future activation that's still missing required
        fields. Rather than force these into a bucket that misrepresents them,
        they get their own honest label.
    """
    date = row["activation_date"]
    required_ok = all(
        str(row[field]).strip() not in ("Unknown", "Not Reported", "nan", "")
        for field in REQUIRED_FIELDS
    )

    if pd.isna(date):
        return "Incomplete Data"

    days_until = (date - today).days

    if days_until < 0:
        return "Needs Follow-Up"
    if days_until <= 5:
        return "At Risk" if not required_ok else "On Track"
    # more than 5 days out
    if required_ok:
        return "On Track"
    return "Incomplete Data"


def get_activation_statuses(today):
    """Shared logic: activations with a computed status column."""
    df = load_activations().copy()
    df["status"] = df.apply(lambda row: compute_status(row, today), axis=1)
    return df


def render_overview_dashboard(today):
    render_header(
        "Overview Dashboard",
        "Every activation from the Freshers Campaign tracker, color-coded by status.",
    )

    df = get_activation_statuses(today)

    # --- summary row ---
    st.subheader("Summary")
    status_counts = df["status"].value_counts().reindex(
        ["On Track", "At Risk", "Needs Follow-Up", "Incomplete Data"], fill_value=0
    )
    cols = st.columns(5)
    cols[0].metric("Total Activations", len(df))
    for i, status in enumerate(["On Track", "At Risk", "Needs Follow-Up", "Incomplete Data"]):
        cols[i + 1].metric(status, int(status_counts[status]))

    with st.expander("Count by owner (SM Name)"):
        owner_counts = df.groupby("owner_sm_name").size().reset_index(name="activation_count")
        owner_counts = owner_counts.sort_values("activation_count", ascending=False)
        st.dataframe(owner_counts, hide_index=True, width='stretch')

    st.divider()

    # --- color-coded table ---
    st.subheader("All Activations")

    def highlight_status(val):
        color = STATUS_COLORS.get(val, "#FFFFFF")
        return (
            f"background-color: {color}22; color: {color}; font-weight: 700; "
            f"border-radius: 12px; border: 1px solid {color}; text-align: center;"
        )

    display_df = df[[
        "college_name", "owner_sm_name", "primary_or_secondary", "activation_date",
        "status", "integration_plan", "assets_required", "asset_qty", "budget",
    ]].rename(columns={
        "college_name": "College",
        "owner_sm_name": "Owner (SM)",
        "primary_or_secondary": "Primary/Secondary",
        "activation_date": "Activation Date",
        "status": "Status",
        "integration_plan": "Integration Plan",
        "assets_required": "Assets Required",
        "asset_qty": "Asset Qty",
        "budget": "Budget",
    })

    styled = display_df.style.map(highlight_status, subset=["Status"])
    st.dataframe(styled, width='stretch', hide_index=True)

    # --- quick chart ---
    status_df = status_counts.reset_index()
    status_df.columns = ["Status", "Count"]
    fig = px.bar(
        status_df,
        x="Status",
        y="Count",
        color="Status",
        color_discrete_map=STATUS_COLORS,
        title="Activations by Status",
    )
    fig = style_chart(fig)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, width='stretch')


def get_tier_ab_festivals():
    """
    Shared logic (used by both the Risk & Prioritization page and the
    Weekly Summary): returns Tier A/B festivals sorted so flagged/at-risk
    ones come first.
    """
    df = load_fest_tracker().copy()
    tier_a_b = df[df["tier"].isin(["TIER A", "TIER B"])].copy()
    tier_a_b["has_competitor_note"] = tier_a_b["competitor_activity_note"] != "Not Reported"
    tier_a_b["_tier_sort"] = tier_a_b["tier"].map({"TIER A": 0, "TIER B": 1})
    tier_a_b["_risk_sort"] = tier_a_b.apply(
        lambda r: 0 if (r["lost_to_competition_flag"] or r["has_competitor_note"]) else 1,
        axis=1,
    )
    return tier_a_b.sort_values(["_tier_sort", "_risk_sort"])


def render_risk_prioritization():
    render_header(
        "Risk &amp; Prioritization View",
        "Tier A and Tier B festivals from the Fest Tracker, sorted so the "
        "highest-priority at-risk items surface first.",
    )

    tier_a_b = get_tier_ab_festivals()

    # --- summary row ---
    st.subheader("Summary")
    cols = st.columns(4)
    cols[0].metric("Tier A/B Festivals", len(tier_a_b))
    cols[1].metric("Tier A", int((tier_a_b["tier"] == "TIER A").sum()))
    cols[2].metric("Lost to Competition", int(tier_a_b["lost_to_competition_flag"].sum()))
    cols[3].metric("Competitor Activity Noted", int(tier_a_b["has_competitor_note"].sum()))

    st.divider()

    # --- highlighted table ---
    st.subheader("Tier A/B Festivals — Highest Priority First")

    def highlight_row(row):
        # row.name is the original row's index, which survives the column
        # rename below — so we look up the flag from tier_a_b directly
        # instead of from the (renamed) columns in `row` itself.
        original = tier_a_b.loc[row.name]
        if original["lost_to_competition_flag"]:
            color = STATUS_COLORS["Needs Follow-Up"]  # red - already lost
        elif original["has_competitor_note"]:
            color = STATUS_COLORS["At Risk"]  # amber - competitor activity noted
        else:
            color = STATUS_COLORS["On Track"]  # green - no flags
        return [f"background-color: {color}; color: white; border-radius: 4px;"] * len(row)

    display_df = tier_a_b[[
        "region", "city", "institution_name", "fest_name", "month", "tier",
        "crowd_approx", "total_sales", "lost_to_competition_flag",
        "lost_to_competition_note", "competitor_activity_note",
    ]].rename(columns={
        "region": "Region",
        "city": "City",
        "institution_name": "Institution",
        "fest_name": "Fest Name",
        "month": "Month",
        "tier": "Tier",
        "crowd_approx": "Crowd Approx.",
        "total_sales": "Total Sales",
        "lost_to_competition_flag": "Lost to Competition?",
        "lost_to_competition_note": "Loss Reason (if any)",
        "competitor_activity_note": "Competitor Activity Note",
    })

    styled = display_df.style.apply(highlight_row, axis=1)
    st.dataframe(styled, width='stretch', hide_index=True)

    st.caption(
        "🔴 Red = already lost to competition this year. 🟠 Amber = a "
        "competitor-activity note exists but it's not marked lost. 🟢 Green "
        "= no competitor flags on record."
    )


def get_owner_followup_summary(today):
    """
    Shared logic (used by both the Owner/Blocker Log page and the Weekly
    Summary): returns the exploded per-owner dataframe and the owners with
    2+ Needs Follow-Up items.
    """
    df = load_activations().copy()
    df["status"] = df.apply(lambda row: compute_status(row, today), axis=1)
    df["owner_list"] = df["owner_sm_name"].apply(
        lambda v: [name.strip() for name in str(v).split(",") if name.strip()]
    )
    exploded = df.explode("owner_list").rename(columns={"owner_list": "owner"})
    followup_counts = (
        exploded[exploded["status"] == "Needs Follow-Up"]
        .groupby("owner")
        .size()
        .sort_values(ascending=False)
    )
    flagged_owners = followup_counts[followup_counts >= 2]
    return exploded, flagged_owners


def render_owner_blocker_log(today):
    render_header(
        "Owner / Blocker Log",
        "Activations grouped by owner (SM Name), so it's obvious at a "
        "glance who owns what and what's overdue.",
    )

    exploded, flagged_owners = get_owner_followup_summary(today)

    st.subheader("Summary")
    cols = st.columns(3)
    cols[0].metric("Total Owners", exploded["owner"].nunique())
    cols[1].metric("Owners with 2+ Needs Follow-Up", len(flagged_owners))
    cols[2].metric("Total Activations", len(load_activations()))

    if len(flagged_owners) > 0:
        st.warning(
            "⚠️ These owners have 2 or more activations Needing Follow-Up: "
            + ", ".join(f"{name} ({count})" for name, count in flagged_owners.items())
        )

    st.divider()
    st.subheader("Activations by Owner")

    def highlight_status(val):
        color = STATUS_COLORS.get(val, "#FFFFFF")
        return (
            f"background-color: {color}22; color: {color}; font-weight: 700; "
            f"border-radius: 12px; border: 1px solid {color}; text-align: center;"
        )

    owners_sorted = sorted(exploded["owner"].dropna().unique())
    for owner in owners_sorted:
        subset = exploded[exploded["owner"] == owner]
        owner_followup_count = int((subset["status"] == "Needs Follow-Up").sum())
        label = f"{owner} — {len(subset)} activation(s)"
        if owner_followup_count >= 2:
            label += f"  ⚠️ {owner_followup_count} Needs Follow-Up"

        with st.expander(label):
            display_df = subset[[
                "college_name", "activation_date", "status",
                "integration_plan", "assets_required", "budget",
            ]].rename(columns={
                "college_name": "College",
                "activation_date": "Activation Date",
                "status": "Status",
                "integration_plan": "Integration Plan",
                "assets_required": "Assets Required",
                "budget": "Budget",
            })
            styled = display_df.style.map(highlight_status, subset=["Status"])
            st.dataframe(styled, width='stretch', hide_index=True)


def get_roi_tables():
    """
    Shared logic (used by both the ROI Recommendation page and the Weekly
    Summary): returns the cost-per-can and cost-per-attendee tables, sorted
    most to least cost-efficient.
    """
    df = load_events().copy()
    can_df = df[(df["has_cost_data"]) & (df["has_cans_data"]) & (df["cans_sold"] > 0)].copy()
    can_df["cost_per_can"] = can_df["total_cost"] / can_df["cans_sold"]
    can_df = can_df.sort_values("cost_per_can")

    att_df = df[(df["has_cost_data"]) & (df["has_people_data"]) & (df["people_present"] > 0)].copy()
    att_df["cost_per_attendee"] = att_df["total_cost"] / att_df["people_present"]
    att_df = att_df.sort_values("cost_per_attendee")

    return df, can_df, att_df


def render_roi_recommendation():
    render_header(
        "ROI Recommendation Engine",
        "Cost-per-can and cost-per-attendee for each 3P event, computed with "
        "simple transparent math — no machine learning.",
    )

    df, can_df, att_df = get_roi_tables()
    total_events = len(df)

    st.info(
        f"Only {total_events} events are in the tracker in total, and not "
        f"every one has both a recorded cost and a recorded sales/attendee "
        f"figure. The tables below only include events with usable numbers "
        f"for that specific calculation — rows with missing data are left "
        f"out rather than guessed at."
    )

    st.subheader("Cost per Can Sold")
    st.caption(
        f"{len(can_df)} of {total_events} events have both a cost figure "
        f"and a cans-sold figure greater than zero — this is a small sample, "
        f"so treat these as directional, not definitive."
    )
    if len(can_df) > 0:
        can_display = can_df[["event_name", "discipline", "total_cost", "cans_sold", "cost_per_can"]].rename(
            columns={
                "event_name": "Event", "discipline": "Type",
                "total_cost": "Total Cost (₹)", "cans_sold": "Cans Sold",
                "cost_per_can": "Cost per Can (₹)",
            }
        )
        st.dataframe(can_display.style.format({"Cost per Can (₹)": "₹{:.2f}"}), width='stretch', hide_index=True)

        fig = px.bar(
            can_df, x="event_name", y="cost_per_can",
            title="Cost per Can Sold by Event (lower = more efficient)",
            labels={"event_name": "Event", "cost_per_can": "Cost per Can (₹)"},
            color_discrete_sequence=[BRAND_ACCENT],
        )
        fig = style_chart(fig)
        st.plotly_chart(fig, width='stretch')

        best_can = can_df.iloc[0]
        worst_can = can_df.iloc[-1]
        multiple = worst_can["cost_per_can"] / best_can["cost_per_can"]
        st.markdown(
            f"**Calculation:** {worst_can['event_name']} cost ₹{worst_can['total_cost']:.0f} "
            f"and sold {worst_can['cans_sold']:.0f} cans → ₹{worst_can['cost_per_can']:.2f} per can. "
            f"{best_can['event_name']} cost ₹{best_can['total_cost']:.0f} for {best_can['cans_sold']:.0f} "
            f"cans → ₹{best_can['cost_per_can']:.2f} per can. That makes "
            f"**{worst_can['event_name']} roughly {multiple:.1f}x more expensive per can sold** "
            f"than {best_can['event_name']}."
        )

    st.divider()

    st.subheader("Cost per Attendee")
    st.caption(
        f"{len(att_df)} of {total_events} events have both a cost figure and "
        f"an attendee figure greater than zero."
    )
    if len(att_df) > 0:
        att_display = att_df[["event_name", "discipline", "total_cost", "people_present", "cost_per_attendee"]].rename(
            columns={
                "event_name": "Event", "discipline": "Type",
                "total_cost": "Total Cost (₹)", "people_present": "People Present",
                "cost_per_attendee": "Cost per Attendee (₹)",
            }
        )
        st.dataframe(att_display.style.format({"Cost per Attendee (₹)": "₹{:.3f}"}), width='stretch', hide_index=True)

        fig2 = px.bar(
            att_df, x="event_name", y="cost_per_attendee",
            title="Cost per Attendee by Event (lower = more efficient)",
            labels={"event_name": "Event", "cost_per_attendee": "Cost per Attendee (₹)"},
            color_discrete_sequence=[BRAND_LINK],
        )
        fig2 = style_chart(fig2)
        st.plotly_chart(fig2, width='stretch')

        best_att = att_df.iloc[0]
        worst_att = att_df.iloc[-1]
        multiple_att = worst_att["cost_per_attendee"] / best_att["cost_per_attendee"]
        st.markdown(
            f"**Calculation:** {worst_att['event_name']} cost ₹{worst_att['total_cost']:.0f} "
            f"for {worst_att['people_present']:.0f} attendees → ₹{worst_att['cost_per_attendee']:.3f} "
            f"per attendee. {best_att['event_name']} cost ₹{best_att['total_cost']:.0f} for "
            f"{best_att['people_present']:.0f} attendees → ₹{best_att['cost_per_attendee']:.3f} "
            f"per attendee. That makes **{worst_att['event_name']} roughly {multiple_att:.1f}x more "
            f"expensive per attendee reached** than {best_att['event_name']}."
        )

    st.divider()
    st.subheader("Recommendation")
    st.write(
        f"Based on cost-per-can, **{worst_can['event_name']}** ({worst_can['discipline']}) "
        f"is the least efficient format on record for direct sales conversion, at roughly "
        f"{multiple:.1f}x the cost per can of the most efficient event. Based on "
        f"cost-per-attendee, **{worst_att['event_name']}** ({worst_att['discipline']}) is the "
        f"least efficient for reach, at roughly {multiple_att:.1f}x the cost per attendee of "
        f"the most efficient event. Recommend deprioritizing these formats unless the goal is "
        f"brand visibility rather than direct sales conversion — and note that with only "
        f"{len(can_df)} events having usable cans-sold data, this conclusion should be "
        f"revisited as more events report full numbers."
    )


def build_weekly_summary_text(today, file_format):
    """
    Builds the plain-English weekly review summary as a string, pulling the
    exact same numbers shown on the other 4 pages. file_format is "md" or
    "txt" - md gets markdown headers/bold, txt gets plain dashes/caps.
    """
    lines = []

    def h1(text):
        lines.append(f"# {text}" if file_format == "md" else f"{text}\n{'=' * len(text)}")

    def h2(text):
        lines.append(f"## {text}" if file_format == "md" else f"\n{text}\n{'-' * len(text)}")

    def bold(text):
        return f"**{text}**" if file_format == "md" else text.upper()

    generated_on = dt.date.today().strftime("%d %b %Y")
    h1("Weekly Review Summary — Red Bull Campus Activation Command Center")
    lines.append(f"Generated on {generated_on} | Simulated 'today' for status logic: {today.strftime('%d %b %Y')}")
    lines.append("")

    # --- Section 1: status counts (Feature 1) ---
    h2("1. Activation Status Overview")
    df = get_activation_statuses(today)
    status_counts = df["status"].value_counts().reindex(
        ["On Track", "At Risk", "Needs Follow-Up", "Incomplete Data"], fill_value=0
    )
    lines.append(f"Total activations: {len(df)}")
    for status in ["On Track", "At Risk", "Needs Follow-Up", "Incomplete Data"]:
        lines.append(f"  - {status}: {int(status_counts[status])}")
    lines.append("")

    # --- Section 2: top at-risk Tier A festivals (Feature 2) ---
    h2("2. Top At-Risk Tier A Festivals")
    tier_a_b = get_tier_ab_festivals()
    flagged = tier_a_b[tier_a_b["lost_to_competition_flag"] | tier_a_b["has_competitor_note"]]
    tier_a_flagged = flagged[flagged["tier"] == "TIER A"]
    if len(tier_a_flagged) == 0:
        lines.append("No Tier A festivals are currently flagged as lost or at risk.")
    else:
        for _, row in tier_a_flagged.iterrows():
            reason = "lost to competition" if row["lost_to_competition_flag"] else "competitor activity noted"
            lines.append(f"  - {bold(row['fest_name'])} at {row['institution_name']} ({reason})")
    lines.append("")

    # --- Section 3: owners with 2+ overdue items (Feature 3) ---
    h2("3. Owners Needing Attention (2+ overdue items)")
    _, flagged_owners = get_owner_followup_summary(today)
    if len(flagged_owners) == 0:
        lines.append("No owner currently has 2 or more activations needing follow-up.")
    else:
        for name, count in flagged_owners.items():
            lines.append(f"  - {bold(name)}: {count} activations needing follow-up")
    lines.append("")

    # --- Section 4: single highest-impact recommendation (Feature 4) ---
    h2("4. Highest-Impact ROI Recommendation")
    _, can_df, att_df = get_roi_tables()
    if len(can_df) > 0 and len(att_df) > 0:
        can_multiple = can_df.iloc[-1]["cost_per_can"] / can_df.iloc[0]["cost_per_can"]
        att_multiple = att_df.iloc[-1]["cost_per_attendee"] / att_df.iloc[0]["cost_per_attendee"]
        if att_multiple >= can_multiple:
            worst, best = att_df.iloc[-1], att_df.iloc[0]
            lines.append(
                f"{bold(worst['event_name'])} ({worst['discipline']}) costs roughly "
                f"₹{worst['cost_per_attendee']:.2f} per attendee reached, about "
                f"{att_multiple:.1f}x higher than the most efficient event on record, "
                f"{best['event_name']} (₹{best['cost_per_attendee']:.2f} per attendee). "
                f"Recommend deprioritizing this format unless the goal is brand "
                f"visibility rather than direct reach efficiency."
            )
        else:
            worst, best = can_df.iloc[-1], can_df.iloc[0]
            lines.append(
                f"{bold(worst['event_name'])} ({worst['discipline']}) costs roughly "
                f"₹{worst['cost_per_can']:.2f} per can sold, about {can_multiple:.1f}x "
                f"higher than the most efficient event on record, {best['event_name']} "
                f"(₹{best['cost_per_can']:.2f} per can). Recommend deprioritizing this "
                f"format unless the goal is brand visibility rather than direct sales "
                f"conversion."
            )
        lines.append(
            f"(Note: only {len(can_df)} of {len(load_events())} events have usable "
            f"cans-sold data — treat this as directional.)"
        )
    else:
        lines.append("Not enough events have usable cost + sales/attendee data to compute a recommendation yet.")

    return "\n".join(lines)


def render_weekly_summary(today):
    render_header(
        "Weekly Review Summary",
        "Combines the highlights from all four views above into one "
        "downloadable summary for a status meeting.",
    )

    file_format = st.radio("Export format:", ["Markdown (.md)", "Plain text (.txt)"], horizontal=True)
    fmt_code = "md" if "md" in file_format else "txt"

    summary_text = build_weekly_summary_text(today, fmt_code)

    st.subheader("Preview")
    st.text(summary_text)

    extension = "md" if fmt_code == "md" else "txt"
    st.download_button(
        label=f"⬇️ Download as .{extension}",
        data=summary_text,
        file_name=f"weekly_review_summary.{extension}",
        mime="text/markdown" if fmt_code == "md" else "text/plain",
    )


# ---------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div class="rb-sidebar-brand">
        <div class="rb-mark">RB</div>
        <div>
            <div class="rb-brand-text">Campus Activation<br>Command Center</div>
            <div class="rb-brand-sub">Red Bull Student Marketeer Program</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- shared "simulate today" control, used by any page that needs to know
# what "today" is (all real activation dates are from 2025) ---
default_today = dt.date(2025, 8, 15)  # roughly the middle of the real data's date range
today = st.sidebar.date_input(
    "Simulate today's date as:",
    value=default_today,
    help="All activation dates in this dataset are from 2025. This lets "
    "you view the dashboard as it would have looked on any given day, "
    "without changing any underlying data.",
)
st.sidebar.divider()

PAGES = {
    "Overview Dashboard": lambda: render_overview_dashboard(today),
    "Risk & Prioritization": render_risk_prioritization,
    "Owner / Blocker Log": lambda: render_owner_blocker_log(today),
    "ROI Recommendation Engine": render_roi_recommendation,
    "Weekly Review Summary": lambda: render_weekly_summary(today),
}

selected_page = st.sidebar.radio("Go to:", list(PAGES.keys()))
st.sidebar.divider()

PAGES[selected_page]()
