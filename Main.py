import streamlit as st
import pandas as pd
import plotly.express as px

# Updated Sample Project Data
data = {
    'Task': ['Engineering Design', 'Permitting', 'Procurement', 'Site Preparation', 'Module Installation', 'Electrical Work', 'Commissioning'],
    'Start Date': ['2024-01-15', '2024-02-01', '2024-03-15', '2024-04-01', '2024-05-01', '2024-06-15', '2024-07-15'],
    'End Date': ['2024-02-28', '2024-03-31', '2024-04-30', '2024-04-15', '2024-06-30', '2024-07-14', '2024-08-01'],
    'Percent Complete': [95, 80, 60, 100, 30, 0, 0],
    'Category': ['Engineering', 'Legal', 'Procurement', 'Construction', 'Construction', 'Electrical', 'Commissioning'],
    'Budget': [100000, 50000, 500000, 200000, 800000, 150000, 100000],
    'Actual Cost': [98000, 42000, 320000, 195000, 250000, 0, 0],
    'System Size (kWp)': [0, 0, 0, 0, 1500, 0, 0],
    'Energy Production (kWh)': [0, 0, 0, 0, 12000, 0, 0],  # Sample energy production data
    'Temperature (°C)': [25, 22, 28, 32, 35, 31, 29],     # Sample temperature data
}

# Create DataFrame and handle NaN values
df = pd.DataFrame(data)
df['Cost Variance'] = df['Budget'] - df['Actual Cost']
df.fillna(0, inplace=True)  # Fill any missing values with 0
# Convert date columns to datetime
df['Start Date'] = pd.to_datetime(df['Start Date'])
df['End Date'] = pd.to_datetime(df['End Date'])

# --- Project Overview ---
st.header("Solar Project Dashboard")

st.subheader("Project Details")
st.write(f"**Client:** SolarCorp")
st.write(f"**Project Name:** Sunny Acres Solar Farm")
st.write(f"**Location:** Arizona, USA")
st.write(f"**Start Date:** {df['Start Date'].min()}")
st.write(f"**End Date:** {df['End Date'].max()}")
st.write(f"**System Size (kWp):** {df['System Size (kWp)'].sum()}")

# --- Filters (Sidebar) ---
st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Filter by Category", df['Category'].unique())
start_time = df['Start Date'].min().to_pydatetime()
end_time = df['End Date'].max().to_pydatetime()

start_date, end_date = st.sidebar.slider(
    "Select Date Range",
    value=(start_time, end_time),
    format="YYYY-MM-DD")

task_filter = st.sidebar.text_input("Search Tasks")

# Apply filters to the dataframe (convert back to Timestamps)
filtered_df = df[
    (df['Category'].isin(selected_categories)) &
    (df['Start Date'] >= pd.Timestamp(start_date)) &
    (df['End Date'] <= pd.Timestamp(end_date))      &
    (df['Task'].str.contains(task_filter, case=False))
]

# --- Dashboard with Tabs ---
tab1, tab2, tab3 = st.tabs(["Progress Overview", "Financial Tracking", "Risk Management"])

with tab1:
    # --- Progress Tracking ---
    st.subheader("Project Progress")
    if not filtered_df.empty:
        overall_progress = filtered_df['Percent Complete'].mean() / 100
    else:
        overall_progress = 0
    st.progress(overall_progress)
    st.write(f"Overall Project Progress (Filtered): {overall_progress * 100:.1f}%")

    # Gantt Chart with Task Progress
    fig_gantt = px.timeline(filtered_df, x_start="Start Date", x_end="End Date", y="Task", color="Category")
    fig_gantt.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_gantt, use_container_width=True)

    # Individual Task Progress Bars
    st.subheader("Task Progress")
    for index, row in filtered_df.iterrows():
        st.write(f"{row['Task']}:")
        st.progress(row['Percent Complete'] / 100)

    # Energy Production Line Chart
    st.subheader("Energy Production")
    fig_energy = px.line(filtered_df, x='End Date', y='Energy Production (kWh)', title='Cumulative Energy Production')
    st.plotly_chart(fig_energy)

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

# --- Timeline ---
st.subheader("Project Timeline")
fig_timeline = px.timeline(df, x_start="Start Date", x_end="End Date", y="Task", color="Category")
fig_timeline.update_yaxes(autorange="reversed")
st.plotly_chart(fig_timeline)  # Interactive timeline

# --- Key Metrics Summary ---
st.subheader("Key Metrics")
st.write(f"**Total Tasks:** {len(df)}")
st.write(f"**Tasks Completed:** {df['Percent Complete'].value_counts().get(100, 0)}")

