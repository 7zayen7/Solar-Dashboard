import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_extras.metric_cards import style_metric_cards

# Function to load data and process it
def load_and_process_data(filename='solar_project_data.xlsx'):
    try:
        df = pd.read_excel(filename)
        df['Cost Variance'] = df['Budget'] - df['Actual Cost']
        df.fillna(0, inplace=True)
        df['Start Date'] = pd.to_datetime(df['Start Date'])
        df['End Date'] = pd.to_datetime(df['End Date'])
        return df
    except FileNotFoundError:
        st.error(f"Error: File '{filename}' not found in the current directory.")
        st.stop()


# --- Initialize session state ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

# --- Load data initially ---
if st.session_state.df.empty:
    df = load_and_process_data()
    st.session_state.df = df


# --- Callback to refresh data when a button is clicked ---
def refresh_data():
    st.session_state.df = load_and_process_data()


# --- Refresh Button ---
st.button("Refresh Data", on_click=refresh_data)

# --- Project Overview ---
st.header("NEOM Bay Airport Project Dashboard")

st.subheader("Project Details")
if not st.session_state.df.empty:
    st.write(f"**Client:** NEOM")
    st.write(f"**Project Name:** NEOM Bay Airport")
    st.write(f"**Location:** NEOM, KSA")
    st.write(f"**Start Date:** {st.session_state.df['Start Date'].min()}")
    st.write(f"**End Date:** {st.session_state.df['End Date'].max()}")
    #st.write(f"**System Size (kWp):** {st.session_state.df['System Size (kWp)'].sum()}")
else:
    st.warning("No data found in the Excel file.")

# --- Filters (Sidebar) ---
# Moved the filters section after loading and processing the data
st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Filter by Category", st.session_state.df['Category'].unique())
start_time = st.session_state.df['Start Date'].min().to_pydatetime()
end_time = st.session_state.df['End Date'].max().to_pydatetime()

start_date, end_date = st.sidebar.slider(
    "Select Date Range",
    value=(start_time, end_time),
    format="YYYY-MM-DD")

task_filter = st.sidebar.text_input("Search Tasks")

# Apply filters to the dataframe (convert back to Timestamps)
filtered_df = st.session_state.df[
    (st.session_state.df['Category'].isin(selected_categories)) &
    (st.session_state.df['Start Date'] >= pd.Timestamp(start_date)) &
    (st.session_state.df['End Date'] <= pd.Timestamp(end_date)) &
    (st.session_state.df['Task'].str.contains(task_filter, case=False))
    ]

# --- Dashboard with Tabs ---
tab1, tab2, tab3 = st.tabs(["Progress Overview", "Financial Tracking", "Risk Management"])

with tab1:
    # --- Progress Tracking ---
    st.subheader("Project Progress")

    # --- KPI cards for metrics ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
            f'<span style="color:black">Total Tasks: {len(st.session_state.df)}  <span style="font-size:smaller;">({len(filtered_df)} filtered)</span></span>'
            '</div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
            f'<span style="color:black">Tasks Completed: {st.session_state.df["Percent Complete"].value_counts().get(100, 0)}</span>'
            '</div>',
            unsafe_allow_html=True
        )

    with col3:
        if not filtered_df.empty:
            overall_progress = filtered_df['Percent Complete'].mean() / 100
            st.markdown(
                f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
                f'<span style="color:black">Overall Progress: {overall_progress * 100:.1f}%</span>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
                f'<span style="color:black">Overall Progress: No data available</span>'
                '</div>',
                unsafe_allow_html=True
            )
    style_metric_cards()

    # Gantt Chart with Task Progress
    fig_gantt = px.timeline(filtered_df, x_start="Start Date", x_end="End Date", y="Task", color="Category")
    fig_gantt.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_gantt, use_container_width=True)

    # Individual Task Progress Bars
    st.subheader("Task Progress")
    for index, row in filtered_df.iterrows():
        st.write(f"{row['Task']}:")
        st.progress(row['Percent Complete'] / 100)

        # --- Energy Production and Temperature Heatmap ---
    if not filtered_df.empty and ('Energy Production (kWh)' in filtered_df.columns) and (
            'Temperature (°C)' in filtered_df.columns):
        fig_heatmap = px.density_heatmap(filtered_df, x='End Date', y='Temperature (°C)', z='Energy Production (kWh)',
                                         title='Energy Production vs. Temperature')
        st.plotly_chart(fig_heatmap)
    else:
        st.write("Insufficient data for energy/temperature heatmap.")

with tab2:
    # --- Financial Tracking ---
    st.subheader("Financial Overview")

    # Calculate filtered totals, handling empty DataFrame
    total_budget = filtered_df['Budget'].sum() if not filtered_df.empty else 0
    total_actual_cost = filtered_df['Actual Cost'].sum() if not filtered_df.empty else 0
    total_cost_variance = total_budget - total_actual_cost

    st.write(f"**Total Budget (Filtered):** ${total_budget}")
    st.write(f"**Total Actual Cost (Filtered):** ${total_actual_cost}")
    st.write(f"**Total Cost Variance (Filtered):** ${total_cost_variance}")

    # Budget Allocation Pie Chart
    if not filtered_df.empty:
        fig_budget = px.pie(filtered_df, values='Budget', names='Category', title='Budget Allocation')
        st.plotly_chart(fig_budget)
    else:
        st.write("No data to display for budget allocation.")

    # Cost Comparison Bar Chart
    if not filtered_df.empty:
        cost_df = filtered_df.melt(id_vars='Task', value_vars=['Budget', 'Actual Cost'])
        fig_cost = px.bar(cost_df, x='Task', y='value', color='variable', barmode='group', title='Cost Comparison')
        st.plotly_chart(fig_cost)
    else:
        st.write("No data to display for cost comparison.")

        # --- Projected vs. Actual Cost Bar Chart ---
        if not filtered_df.empty:
            cost_df = filtered_df.melt(id_vars='Task', value_vars=['Budget', 'Actual Cost'])
            fig_cost = px.bar(cost_df, x='Task', y='value', color='variable', barmode='group',
                              title='Cost Comparison: Projected vs. Actual')
            st.plotly_chart(fig_cost)

    # Detailed Financial Table
    st.subheader('Financial Details')
    if not filtered_df.empty:
        st.table(filtered_df[['Task', 'Budget', 'Actual Cost', 'Cost Variance']])
    else:
        st.write("No financial data to display.")

    # Data Exploration Table
    st.subheader("Data Table")
    st.write(filtered_df)

with tab3:
    # --- Risk Management ---
    st.subheader("Risk Management")

    risk_data = {
        'Risk': ['Material delays', 'Weather disruptions', 'Permitting issues', 'Labor shortage'],
        'Probability': ['Medium', 'High', 'Low', 'Medium'],
        'Impact': ['High', 'Medium', 'Medium', 'Low'],
        'Mitigation Plan': ['Secure backup suppliers', 'Contingency schedule', 'Proactive communication', 'Cross-training']
    }

    st.table(pd.DataFrame(risk_data))

    # --- Data Exploration Table ---
    st.subheader("Data Table")
    st.write(filtered_df)

# --- Key Metrics Summary ---
st.subheader("Key Metrics")
st.write(f"**Total Tasks:** {len(st.session_state.df)}")  #Access df from the session state
st.write(f"**Tasks Completed:** {st.session_state.df['Percent Complete'].value_counts().get(100, 0)}")

if not filtered_df.empty:
    overall_progress = filtered_df['Percent Complete'].mean() / 100
    st.write(f"**Overall Project Progress (Filtered):** {overall_progress * 100:.1f}%")
else:
    st.write("**Overall Project Progress (Filtered):** No data available.")


# --- Timeline ---
st.subheader("Project Timeline")
fig_timeline = px.timeline(st.session_state.df, x_start="Start Date", x_end="End Date", y="Task", color="Category")
fig_timeline.update_yaxes(autorange="reversed")
st.plotly_chart(fig_timeline)  # Interactive timeline
