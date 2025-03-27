"""Streamlit dashboard for displaying agent metrics and trends."""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any
from core.monitoring import metrics_collector

def setup_page():
    """Setup the Streamlit page configuration."""
    st.set_page_config(
        page_title="Agent Performance Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
def display_kpi_cards(trends: Dict[str, Any]):
    """Display KPI cards at the top of the dashboard."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Task Velocity",
            f"{trends['velocity']['current']:.0f}",
            f"{trends['velocity']['trend']:.1f}",
            help="Tasks completed per day"
        )
        
    with col2:
        st.metric(
            "Error Rate",
            f"{trends['error_trends']['current_rate']:.1%}",
            f"{trends['error_trends']['trend']:.1%}",
            help="Percentage of failed tasks"
        )
        
    with col3:
        st.metric(
            "Retry Efficiency",
            f"{trends['retry_efficiency']['efficiency']:.1%}",
            f"{trends['retry_efficiency']['retry_rate']:.1%}",
            help="Success rate of retries"
        )
        
    with col4:
        total_tasks = sum(
            kpi['total_tasks'] 
            for kpi in trends['agent_kpis'].values()
        )
        st.metric(
            "Total Tasks",
            f"{total_tasks}",
            "Last 7 days",
            help="Total tasks processed"
        )
        
def display_velocity_chart(trends: Dict[str, Any]):
    """Display task velocity trend chart."""
    st.subheader("Task Velocity Trend")
    
    # Create DataFrame for the chart
    dates = pd.date_range(
        datetime.now().date() - timedelta(days=6),
        datetime.now().date()
    )
    df = pd.DataFrame({
        'Date': dates,
        'Tasks Completed': trends['velocity']['daily_velocities']
    })
    
    fig = px.line(
        df,
        x='Date',
        y='Tasks Completed',
        title='Daily Task Completion Trend'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
def display_error_trends(trends: Dict[str, Any]):
    """Display error rate trends."""
    st.subheader("Error Rate Trends")
    
    # Create DataFrame for the chart
    dates = pd.date_range(
        datetime.now().date() - timedelta(days=6),
        datetime.now().date()
    )
    df = pd.DataFrame({
        'Date': dates,
        'Error Rate': trends['error_trends']['daily_rates']
    })
    
    fig = px.line(
        df,
        x='Date',
        y='Error Rate',
        title='Daily Error Rate Trend'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
def display_agent_kpis(trends: Dict[str, Any]):
    """Display KPIs for each agent."""
    st.subheader("Agent Performance")
    
    # Create DataFrame for agent KPIs
    kpis = trends['agent_kpis']
    df = pd.DataFrame.from_dict(kpis, orient='index')
    
    # Display metrics table
    st.dataframe(
        df.style.format({
            'completion_rate': '{:.1%}',
            'error_rate': '{:.1%}',
            'retry_rate': '{:.1%}',
            'avg_duration': '{:.1f}s'
        })
    )
    
    # Create agent comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            df,
            y=['completion_rate', 'error_rate'],
            title='Agent Success/Error Rates',
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        fig = px.bar(
            df,
            y='avg_duration',
            title='Average Task Duration by Agent'
        )
        st.plotly_chart(fig, use_container_width=True)
        
def display_retry_metrics(trends: Dict[str, Any]):
    """Display retry efficiency metrics."""
    st.subheader("Retry Performance")
    
    retry_metrics = trends['retry_efficiency']
    
    # Create gauge chart for retry efficiency
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=retry_metrics['efficiency'] * 100,
        title={'text': "Retry Success Rate"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "lightgray"},
                {'range': [33, 66], 'color': "gray"},
                {'range': [66, 100], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': retry_metrics['efficiency'] * 100
            }
        }
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display retry statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Retries",
            retry_metrics['total_retries'],
            help="Total number of retry attempts"
        )
        
    with col2:
        st.metric(
            "Successful Retries",
            retry_metrics['successful_retries'],
            help="Number of successful retries"
        )
        
def main():
    """Main entry point for the dashboard."""
    setup_page()
    
    st.title("Agent Performance Dashboard")
    
    # Collect and process metrics
    metrics_collector.collect_daily_metrics()
    dashboard_data = metrics_collector.generate_dashboard_data()
    trends = dashboard_data['trends']
    
    # Display dashboard sections
    display_kpi_cards(trends)
    
    st.divider()
    display_velocity_chart(trends)
    
    st.divider()
    display_error_trends(trends)
    
    st.divider()
    display_agent_kpis(trends)
    
    st.divider()
    display_retry_metrics(trends)
    
    # Add refresh button
    if st.button("Refresh Metrics"):
        st.experimental_rerun()
        
if __name__ == "__main__":
    main() 