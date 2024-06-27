import streamlit as st
from streamlit.components.v1 import html
import pandas as pd
import plotly.express as px
from streamlit_extras.metric_cards import style_metric_cards
import webbrowser
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import datetime
import pdfkit
import base64
import hashlib
import json
from io import BytesIO
import contextlib
import io
from io import StringIO
import uuid

# --- Constants ---
EXCEL_FILENAME = 'solar_project_data.xlsx'

# --- File Watcher (Optional) ---
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == os.path.abspath(EXCEL_FILENAME):
            st.session_state.df = load_and_process_data()
            st.experimental_rerun()  # Refresh the app


# --- Function to open Excel file ---
def edit_excel_file():
    file_path = os.path.abspath(EXCEL_FILENAME)
    webbrowser.open(file_path)

# --- Data Loading and Processing ---
def load_and_process_data(filename='solar_project_data.xlsx'):
    try:
        df = pd.read_excel(filename)
        df['Cost Variance'] = df['Budget'] - df['Actual Cost']
        df.fillna(0, inplace=True)
        df['Start Date'] = pd.to_datetime(df['Start Date'])
        df['End Date'] = pd.to_datetime(df['End Date'])
        return df
    except FileNotFoundError:
        st.error(f"Error: File '{filename}' not found. Make sure it's in the same directory as this script.")
        st.stop()

# --- Session State Initialization ---
if 'df' not in st.session_state:
    st.session_state.df = load_and_process_data()

# --- Refresh Function ---
def refresh_data():
    st.session_state.df = load_and_process_data()

# --- Refresh Button and Edit Button ---
col1, col2 = st.columns(2)
with col1:
    st.button("Refresh Data", on_click=refresh_data)  # Pass the function
with col2:
    st.button("Edit Excel File", on_click=edit_excel_file)

# --- Add Logo ---
col1, col2 = st.columns(2)
with col1:
    logo_path = "dt arabic logo .png" # Make sure your logo is in the same directory or provide the full path
    st.image(logo_path, width=200)  # Adjust width as needed
with col2:
    logo_path = "Neom.png" # Make sure your logo is in the same directory or provide the full path
    st.image(logo_path, width=200)  # Adjust width as needed

# --- Project Overview ---
st.header("NEOM Bay Airport Project Dashboard")
st.subheader("Project Details")
if not st.session_state.df.empty:
    st.write(f"**Client:** NEOM")
    st.write(f"**Project Name:** NEOM Bay Airport")
    st.write(f"**Location:** NEOM, KSA")
    st.write(f"**Start Date:** {st.session_state.df['Start Date'].min().date()}")
    st.write(f"**End Date:** {st.session_state.df['End Date'].max().date()}")
else:
    st.warning("No data found. Please check the Excel file.")


# --- Sidebar Filters ---
st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Filter by Category", st.session_state.df['Category'].unique())
task_filter = st.sidebar.text_input("Search Tasks")
start_time = st.session_state.df['Start Date'].min().date()
end_time = st.session_state.df['End Date'].max().date()
start_date, end_date = st.sidebar.date_input("Select Date Range", value=(start_time, end_time))

# Apply filters directly to session state data
filtered_df = st.session_state.df[
    (st.session_state.df['Category'].isin(selected_categories)) &
    (st.session_state.df['Task'].str.contains(task_filter, case=False)) &
    (st.session_state.df['Start Date'].dt.date >= start_date) &
    (st.session_state.df['End Date'].dt.date <= end_date)
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
    st.subheader("Project Timeline")
    fig_gantt = px.timeline(filtered_df, x_start="Start Date", x_end="End Date", y="Task", color="Category")
    fig_gantt.update_yaxes(autorange="reversed") # Update the fig_gantt before using it
    st.plotly_chart(fig_gantt, use_container_width=True)

    # Individual Task Progress Bars with Percentages and Alerts
    st.subheader("Task Progress")
    for index, row in filtered_df.iterrows():
        task_name = row['Task']
        percent_complete = row['Percent Complete']
        end_date = row['End Date']

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{task_name}:**")
        with col2:
            st.progress(percent_complete / 100)
        with col3:
            st.write(f"{percent_complete:.1f}%")

        # Add Alert
        if percent_complete < 100 and end_date < datetime.datetime.now():  # Check for deadline exceeded
            st.warning(f"⚠️ Task '{task_name}' is overdue and not complete!")

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
