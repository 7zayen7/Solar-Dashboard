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

# --- Add Logo ---
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        """
        <style>
        .logo-container {  # Add a container for the image
            display: flex;
            justify-content: center;  # Center horizontally
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    logo_path = "dt arabic logo .png"
    with st.container():  # Use the container for centering
        st.image(logo_path, width=300)

with col2:
    st.markdown(
        """
        <style>
        .logo-container {  # Add a container for the image
            display: flex;
            justify-content: center;  # Center horizontally
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    logo_path = "Neom.png"
    with st.container():  # Use the container for centering
        st.image(logo_path, width=100)

# --- Constants ---
EXCEL_FILENAME = {'solar_project_data.xlsx','Procurement.xlsx', 'risk.xlsx', 'project_overview.xlsx'}

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
df = st.session_state.df

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

# --- Report Generation ---
def generate_pdf_report(filtered_df):
    """Generates a PDF report from the filtered DataFrame."""

    # Create HTML content with the filtered data and any desired formatting
    html_string = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Report - {datetime.datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            /* CSS for Styling */
            body {{ font-family: sans-serif; color: #333; }}
            h1, h2 {{ color: #007bff; }} /* Blue headings */
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            th {{ background-color: #f0f0f0; }} 
            .alert {{ padding: 10px; margin-bottom: 10px; border-radius: 5px; }}
            .alert-warning {{ background-color: #fff3cd; border-color: #ffeeba; color: #856404; }}
            .alert-danger {{ background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }}
            .alert-success {{ background-color: #d4edda; border-color: #c3e6cb; color: #155724; }}
        </style>
    </head>
    <body>
        <h1>Project Report - NEOM Bay Airport</h1>
        <h2>Key Metrics</h2>
        <p><b>Total Tasks:</b> {len(st.session_state.df)}</p>
        <p><b>Tasks Completed:</b> {st.session_state.df['Percent Complete'].value_counts().get(100, 0)}</p>

        <h2>Financial Details</h2>
        {filtered_df[['Task', 'Budget', 'Actual Cost', 'Cost Variance']].to_html(index=False)}

        <h2>Gantt Chart</h2>
        <div style="display: flex; justify-content: center; align-items: center;">
            <img style="width: 80%;" src='data:image/png;base64,{base64.b64encode(create_gantt_chart(filtered_df)).decode()}' />
        </div>
        
        <h2>Task Progress</h2>

        <table>
            <thead>
                <tr>
                    <th>Task</th>
                    <th>Progress</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {generate_task_progress_table(filtered_df)}
            </tbody>
        </table>

        <h2>Cost Comparison Chart</h2>
        <div style="display: flex; justify-content: center; align-items: center;">
            <img style="width: 80%;" src='data:image/png;base64,{base64.b64encode(create_cost_comparison_chart(filtered_df)).decode()}' />
        </div>

        <h2>Budget Allocation Chart</h2>
        <div style="display: flex; justify-content: center; align-items: center;">
            <img style="width: 80%;" src='data:image/png;base64,{base64.b64encode(create_budget_allocation_chart(filtered_df)).decode()}' />
        </div>
       <h2>Cost Variance Alerts</h2>
        {generate_cost_variance_alerts(filtered_df)}
    </body>
    </html>
    """

    # EVM Metrics Section (Added)
    evm_metrics_html = f"""
       <h2>Earned Value Management (EVM) Metrics</h2>
       <table style="width:50%"> 
           <tr>
               <th>Metric</th>
               <th>Value</th>
           </tr>
           <tr>
               <td>Schedule Variance (SV)</td>
               <td>{project_sv:.2f} $</td>
           </tr>
           <tr>
               <td>Cost Variance (CV)</td>
               <td>{project_cv:.2f} $</td>
           </tr>
           <tr>
               <td>Schedule Performance Index (SPI)</td>
               <td>{project_spi:.2f}</td>
           </tr>
           <tr>
               <td>Cost Performance Index (CPI)</td>
               <td>{project_cpi:.2f}</td>
           </tr>
       </table>
       """

    # Procurement Summary Section (New)
    procurement_summary_html = f"""
    <h2>Procurement Summary</h2>
    <p><b>Total Purchase Orders:</b> {len(procurement_df)}</p>
    <p><b>Total Procurement Cost:</b> ${procurement_df['Total Cost'].sum():.2f}</p>

    <h3>Purchase Orders</h3>
    {procurement_df.to_html(index=False, classes='procurement-table')}
    """

    # Cost Over Time Chart (Procurement) with color scheme and size control
    cost_over_time_data = (
        procurement_df.groupby(pd.Grouper(key='Order Date', freq='M'))['Total Cost']
        .sum()
        .reset_index()
    )
    fig_cost_over_time = px.line(cost_over_time_data, x='Order Date', y='Total Cost', title='Procurement Cost Over Time', color_discrete_sequence=px.colors.qualitative.Plotly)
    fig_cost_over_time.update_layout(
        width=1200,
        height=800,
        xaxis_title='Order Date',
        yaxis_title='Total Cost'
    )

    # PO Status Chart (Procurement) with color scheme and size control
    status_counts = procurement_df['Status'].value_counts()
    fig_status = px.pie(status_counts, values=status_counts.values, names=status_counts.index, title='PO Status', color_discrete_sequence=px.colors.qualitative.Plotly)
    fig_status.update_layout(
        width=1200,
        height=800
    )

    # Inject the procurement section after risk assessment
    html_string = html_string.replace(
        "<h2>Cost Variance Alerts</h2>",
        procurement_summary_html
        + f"<div style='display: flex; justify-content: center; align-items: center;'><img style='width: 80%;' src='data:image/png;base64,{base64.b64encode(fig_cost_over_time.to_image(format='png')).decode()}' /></div>"
        + f"<div style='display: flex; justify-content: center; align-items: center;'><img style='width: 80%;' src='data:image/png;base64,{base64.b64encode(fig_status.to_image(format='png')).decode()}' /></div>"
        + "<h2>Cost Variance Alerts</h2>"
    )

    options = {
        'page-size': 'Letter',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None
    }
    pdf = pdfkit.from_string(html_string, False, options=options)
    return pdf

def generate_task_progress_table(df):
    table_rows = ""
    for _, row in df.iterrows():
        task_name = row['Task']
        percent_complete = row['Percent Complete']
        end_date = row['End Date']

        if percent_complete < 100 and end_date < datetime.datetime.now():
            status = "⚠️ Overdue"
            alert_class = "alert-danger"
        elif 0 < percent_complete < 100:
            status = "🚧 In Progress"
            alert_class = "alert-warning"
        elif percent_complete == 0:
            status = "Not Started"
            alert_class = "alert-warning"
        else:
            status = "✅ Completed"
            alert_class = "alert-success"

        table_rows += f"""
        <tr>
            <td>{task_name}</td>
            <td>
                <div style="background-color: #eee; border-radius: 5px;">
                    <div style="background-color: #4CAF50; width: {percent_complete}%; height: 20px; border-radius: 5px;"></div>
                </div> 
                <span>{percent_complete:.1f}%</span>
            </td>
            <td><div class="alert {alert_class}">{status}</div></td>
        </tr>
        """
    return table_rows

def create_gantt_chart(df):
    # Define a color map for each unique category
    unique_categories = df['Category'].unique()
    color_map = {category: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
                 for i, category in enumerate(unique_categories)}

    # Create the Gantt chart
    fig = px.timeline(df, x_start="Start Date", x_end="End Date", y="Task", color="Category",
                      color_discrete_map=color_map)

    # Update layout and traces for styling
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    fig.update_traces(marker=dict(line=dict(width=2, color='DarkSlateGrey')))
    fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        width=1500,  # Adjust the width as needed
        height=1000  # Adjust the height as needed
    )

    return fig.to_image(format="png")

def generate_cost_variance_alerts(df):
    alerts_html = ""
    for _, row in df.iterrows():
        task_name = row['Task']
        cost_variance = row['Cost Variance']
        if cost_variance == 0:
            alerts_html += f'<div class="alert alert-warning">⚠️ Task "{task_name}" has consumed its entire budget.</div>'
        elif cost_variance < 0:
            alerts_html += f'<div class="alert alert-danger">🚨 Task "{task_name}" has exceeded its budget by ${-cost_variance}.</div>'
        else:
            alerts_html += f'<div class="alert alert-success">✅ Task "{task_name}" has saved ${cost_variance} of its budget.</div>'
    return alerts_html

# Function to create the cost comparison bar chart
def create_cost_comparison_chart(df):
    cost_df = df.melt(id_vars='Task', value_vars=['Budget', 'Actual Cost'])
    fig = px.bar(cost_df, x='Task', y='value', color='variable', barmode='group', title='Cost Comparison',
                 color_discrete_sequence=px.colors.qualitative.Plotly)  # Add color sequence
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    fig.update_layout(
        width=1500,  # Adjust the width as needed
        height=800  # Adjust the height as needed
    )
    return fig.to_image(format="png")

# Function to create the budget allocation pie chart
def create_budget_allocation_chart(df):
    fig = px.pie(df, values='Budget', names='Category', title='Budget Allocation',
                 color_discrete_sequence=px.colors.qualitative.Plotly)  # Add color sequence
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    fig.update_layout(
        width=1500,  # Adjust the width as needed
        height=800  # Adjust the height as needed
    )
    return fig.to_image(format="png")

# --- Refresh Function ---
def refresh_data():
    st.session_state.df = load_and_process_data()  # Refresh solar project data
    st.session_state.project_overview = load_project_overview()  # Refresh project overview data
    st.session_state.risk_df = load_risk_data()  # Refresh risk data
    st.session_state.procurement_df = load_procurement_data()  # Refresh procurement data

# --- Refresh Button and Edit Button ---
col1, col2 = st.columns(2)
with col1:
    st.button("Refresh Data", on_click=refresh_data)  # Pass the function
with col2:
    st.button("Edit Excel File", on_click=edit_excel_file)

# --- Data Loading and Processing for Project Overview ---
def load_project_overview(filename='project_overview.xlsx'):
    df = pd.read_excel(filename)
    return df.set_index("Field")["Value"].to_dict()

# --- Session State Initialization ---
if 'project_overview' not in st.session_state:
    st.session_state.project_overview = load_project_overview()
project_overview = st.session_state.project_overview


# --- Project Overview Section ---
st.header("Saudi Telecom Company PPA Project")
st.subheader("Project Details")
if project_overview:
    for field, value in project_overview.items():
        st.write(f"**{field}:** {value}")
else:
    st.warning("Project overview data not found. Please check the Excel file.")

# --- Dashboard with Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["Progress Overview", "Financial Tracking", "Risk Management", "Procurement Tracking"])

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
    fig_gantt.update_yaxes(autorange="reversed")  # Update the fig_gantt before using it
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

    # Cost Variance Metric Cards with Alerts in a Grid
    if not filtered_df.empty:
        num_columns = 3  # You can adjust the number of columns as needed
        cols = st.columns(num_columns)
        col_index = 0

        for index, row in filtered_df.iterrows():
            cost_variance = row['Cost Variance']
            task_name = row['Task']

            # Create a metric card for each task in the current column
            with cols[col_index]:
                with st.expander(task_name):  # Create an expandable section for each task
                    if cost_variance == 0:
                        st.warning(f"⚠️ Task '{task_name}' has consumed its entire budget.")
                    elif cost_variance < 0:
                        st.error(f"🚨 Task '{task_name}' has exceeded its budget by ${-cost_variance}.")
                    else:
                        st.success(f"✅ Task '{task_name}' has saved ${cost_variance} of its budget.")
            # Move to the next column, wrapping back to the first if necessary
            col_index = (col_index + 1) % num_columns

    # Detailed Financial Table
    st.subheader('Financial Details')
    if not filtered_df.empty:
        st.table(filtered_df[['Task', 'Budget', 'Actual Cost', 'Cost Variance']])
    else:
        st.write("No financial data to display.")

    # EVM Calculations (using 'Budget' as Planned Value)
    st.subheader("Earned Value Management (EVM)")

    # Convert relevant columns to numeric (important!)
    for col in ['Budget', 'Actual Cost', 'Percent Complete']:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

    # Fill NaN values with 0 after conversion
    filtered_df.fillna(0, inplace=True)

    # Calculate EVM metrics for each task and for the project as a whole
    for index, row in filtered_df.iterrows():
        ev = row['Budget'] * (row['Percent Complete'] / 100)
        filtered_df.loc[index, 'EV'] = ev  # Assign 'EV' first
        filtered_df.loc[index, 'SV'] = ev - row['Budget']
        filtered_df.loc[index, 'CV'] = ev - row['Actual Cost']
        filtered_df.loc[index, 'SPI'] = ev / row['Budget'] if row['Budget'] != 0 else 0
        filtered_df.loc[index, 'CPI'] = ev / row['Actual Cost'] if row['Actual Cost'] != 0 else 0

    # Calculate Project Level EVM metrics AFTER the loop
    total_pv = filtered_df['Budget'].sum()  # Using Budget for PV
    total_ev = filtered_df['EV'].sum()
    total_ac = filtered_df['Actual Cost'].sum()
    project_sv = total_ev - total_pv
    project_cv = total_ev - total_ac
    project_spi = total_ev / total_pv if total_pv != 0 else 0
    project_cpi = total_ev / total_ac if total_ac != 0 else 0

    # Create a dictionary to store EVM metrics
    evm_metrics = {
        "Schedule Variance (SV)": f"{project_sv:.2f}",
        "Cost Variance (CV)": f"{project_cv:.2f} $",
        "SPI": f"{project_spi:.2f}",
        "CPI": f"{project_cpi:.2f}"
    }

    # Style the EVM metrics display
    st.markdown(
        """
        <style>
        .evm-metric {
            background-color: black;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
            text-align: center;
        }
        .evm-metric-label {
            font-weight: bold;
            font-size: 18px;
        }
        .evm-metric-value {
            font-size: 24px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Display EVM metrics using st.markdown
    for label, value in evm_metrics.items():
        st.markdown(
            f"""
            <div class="evm-metric">
                <div class="evm-metric-label">{label}</div>
                <div class="evm-metric-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Display EVM metrics table per task
    st.subheader("EVM Metrics per Task")
    st.table(filtered_df[['Task', 'Budget', 'EV', 'Actual Cost', 'SV', 'CV', 'SPI', 'CPI']])  # Display 'Budget'

    # EVM Trend Charts
    st.subheader("EVM Trends Over Time")

    # Prepare data for trend charts (using 'Budget' instead of 'Planned Value')
    trend_df = filtered_df[['Start Date', 'Budget', 'EV', 'Actual Cost']].copy()  # Replace 'Planned Value' with 'Budget'
    trend_df = trend_df.melt(id_vars='Start Date', value_vars=['Budget', 'EV', 'Actual Cost'], var_name='Metric', value_name='Cost')

    # SV Trend Chart (replace 'Planned Value' with 'Budget')
    st.subheader("Schedule Variance (SV) Trend")
    sv_trend = px.line(trend_df[trend_df['Metric'].isin(['Budget', 'EV'])], x='Start Date', y='Cost', color='Metric',
                       title='Schedule Variance Trend')
    st.plotly_chart(sv_trend)

    # CV Trend Chart
    st.subheader("Cost Variance (CV) Trend")
    cv_trend = px.line(trend_df[trend_df['Metric'].isin(['EV', 'Actual Cost'])], x='Start Date', y='Cost', color='Metric',
                       title='Cost Variance Trend')
    st.plotly_chart(cv_trend)

    # SPI and CPI Trend Chart
    st.subheader("SPI and CPI Trends")
    spi_cpi_trend = px.line(filtered_df, x='Start Date', y=['SPI', 'CPI'], title='SPI and CPI Trends')
    st.plotly_chart(spi_cpi_trend)

# --- Data Loading and Processing for Risk Data ---
def load_risk_data(filename='risk.xlsx'):
    df = pd.read_excel(filename)
    return df

with tab3:
    # --- Risk Management ---
    st.header("Risk Management")

    # Load Risk Data
    risk_df = load_risk_data()

    # Risk Table
    st.subheader("Risk Register")
    st.dataframe(risk_df)

    # Risk Matrix
    st.subheader("Risk Matrix")
    fig = px.scatter(risk_df, x="Probability", y="Impact", color="Category",
                     hover_name="Risk Description", title="Risk Matrix",
                     labels={"Probability": "Probability of Occurrence", "Impact": "Impact on Project"})
    st.plotly_chart(fig)

def load_procurement_data(filename='Procurement.xlsx'):
    df = pd.read_excel(filename)
    df['Order Date'] = pd.to_datetime(df['Order Date'])  # Convert to datetime
    df['Delivery Date'] = pd.to_datetime(df['Delivery Date'])
    return df

with tab4:
    st.header("Procurement Dashboard")

    # Load and display data
    procurement_df = load_procurement_data()
    st.subheader("All Purchase Orders")
    st.dataframe(procurement_df)

    # --- KPI cards for metrics ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
            f'<span style="color:black">Total POs: {len(procurement_df)}</span>'
            '</div>',
            unsafe_allow_html=True
        )
    with col2:
        total_cost = procurement_df['Total Cost'].sum()
        st.markdown(
            f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
            f'<span style="color:black">Total Cost: ${total_cost:.2f}</span>'
            '</div>',
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
            f'<span style="color:black">Average Cost/PO: ${total_cost / len(procurement_df):.2f}</span>'
            '</div>',
            unsafe_allow_html=True
        )

    # Total Cost over time graph
    st.subheader("Total Cost Over Time")
    cost_over_time_data = (
        procurement_df.groupby(pd.Grouper(key='Order Date', freq='M'))['Total Cost']
        .sum()
        .reset_index()
    )
    fig_cost_over_time = px.line(cost_over_time_data, x='Order Date', y='Total Cost')
    st.plotly_chart(fig_cost_over_time, use_container_width=True)

    # PO status
    st.subheader('PO Status')
    status_counts = procurement_df['Status'].value_counts()
    fig_status = px.pie(status_counts, values=status_counts.values, names=status_counts.index)
    st.plotly_chart(fig_status)

# --- Report Generation Button ---
st.sidebar.subheader("Generate Report")
if st.sidebar.button("Download PDF Report"):
    if filtered_df.empty:
        st.sidebar.warning("No data to include in the report. Apply filters to select data.")
    else:
        pdf_report = generate_pdf_report(filtered_df)
        # Download report button with a unique file name
        st.sidebar.download_button(
            label="Download PDF Report",
            data=pdf_report,
            file_name=f"NEOM_Bay_Airport_Report_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf",
            mime="application/pdf",
        )

# --- Key Metrics Summary ---
st.subheader("Key Metrics")
st.write(f"**Total Tasks:** {len(st.session_state.df)}")  # Access df from the session state
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

def refresh_data():
    st.session_state.df = load_and_process_data()  # Refresh solar project data
    st.session_state.project_overview = load_project_overview()  # Refresh project overview data
    st.session_state.risk_df = load_risk_data()  # Refresh risk data
    st.session_state.procurement_df = load_procurement_data()  # Refresh procurement data

