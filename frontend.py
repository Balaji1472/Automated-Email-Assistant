"""
Streamlit frontend dashboard for the AI Communication Assistant.
Enhanced with comprehensive data visualization and professional styling.
"""
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
from email_handler import send_email, get_email_counts
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="AI Communication Assistant",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        margin: -1rem -1rem 2rem -1rem;
        padding: 2rem 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e1e5e9;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .urgent-priority {
        border-left: 4px solid #dc3545 !important;
        background-color: #fff8f8;
    }
    .normal-priority {
        border-left: 4px solid #28a745 !important;
        background-color: #f8fff8;
    }
    .negative-sentiment {
        background-color: #fff5f5 !important;
        border: 1px solid #fed7d7;
    }
    .positive-sentiment {
        background-color: #f0fff4 !important;
        border: 1px solid #c6f6d5;
    }
    .neutral-sentiment {
        background-color: #f8f9fa !important;
        border: 1px solid #e9ecef;
    }
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        margin: 3px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .urgent-badge {
        background-color: #dc3545;
        color: white;
    }
    .normal-badge {
        background-color: #28a745;
        color: white;
    }
    .negative-badge {
        background-color: #dc3545;
        color: white;
    }
    .positive-badge {
        background-color: #28a745;
        color: white;
    }
    .neutral-badge {
        background-color: #6c757d;
        color: white;
    }
    .processing-stats {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)


def call_backend() -> Optional[Dict[str, Any]]:
    """Call the backend API to process emails."""
    try:
        response = requests.post(
            "http://127.0.0.1:8000/process-emails",
            timeout=120
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Make sure the FastAPI server is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None


def get_email_statistics():
    """Get email count statistics."""
    try:
        unread_count, read_count = get_email_counts()
        return unread_count, read_count
    except Exception as e:
        st.error(f"Error getting email statistics: {str(e)}")
        return 0, 0


def create_email_overview_charts(unread_count: int, read_count: int) -> None:
    """Create overview charts for email statistics."""
    total_count = unread_count + read_count
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for email status distribution
        if total_count > 0:
            fig_pie = px.pie(
                values=[read_count, unread_count],
                names=['Processed', 'Pending'],
                title='Email Status Distribution',
                color_discrete_sequence=['#28a745', '#ffc107']
            )
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
            fig_pie.update_layout(
                showlegend=True,
                height=300,
                margin=dict(t=50, b=0, l=0, r=0)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No email data available")
    
    with col2:
        # Bar chart for email counts
        fig_bar = go.Figure(data=[
            go.Bar(
                name='Email Counts',
                x=['Total Emails', 'Processed', 'Pending'],
                y=[total_count, read_count, unread_count],
                marker_color=['#6c757d', '#28a745', '#ffc107'],
                text=[total_count, read_count, unread_count],
                textposition='auto'
            )
        ])
        fig_bar.update_layout(
            title='Email Count Overview',
            xaxis_title='Category',
            yaxis_title='Count',
            height=300,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def create_processing_analytics_charts(data: Dict[str, Any]) -> None:
    """Create detailed processing analytics charts."""
    if not data['emails']:
        st.info("No processing data available")
        return
    
    # Prepare data for analysis
    emails_df = pd.DataFrame([
        {
            'priority': email['priority'],
            'sentiment': email['sentiment'],
            'sender_domain': email['sender'].split('@')[-1] if '@' in email['sender'] else 'Unknown',
            'subject_length': len(email['subject']),
            'body_length': len(email['body']),
            'response_length': len(email['draft_response'])
        }
        for email in data['emails']
    ])
    
    # Create subplots
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority vs Sentiment analysis
        priority_sentiment = emails_df.groupby(['priority', 'sentiment']).size().reset_index(name='count')
        fig_heatmap = px.density_heatmap(
            priority_sentiment, 
            x='priority', 
            y='sentiment', 
            z='count',
            title='Priority vs Sentiment Distribution',
            color_continuous_scale='Viridis'
        )
        fig_heatmap.update_layout(height=300)
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col2:
        # Sentiment distribution
        sentiment_counts = emails_df['sentiment'].value_counts()
        fig_sentiment = px.bar(
            x=sentiment_counts.index,
            y=sentiment_counts.values,
            title='Sentiment Analysis Distribution',
            color=sentiment_counts.index,
            color_discrete_map={
                'Positive': '#28a745',
                'Negative': '#dc3545',
                'Neutral': '#6c757d'
            }
        )
        fig_sentiment.update_layout(
            xaxis_title='Sentiment',
            yaxis_title='Count',
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_sentiment, use_container_width=True)
    
    # Additional analytics row
    col3, col4 = st.columns(2)
    
    with col3:
        # Top sender domains
        domain_counts = emails_df['sender_domain'].value_counts().head(5)
        fig_domains = px.bar(
            x=domain_counts.values,
            y=domain_counts.index,
            title='Top Sender Domains',
            orientation='h'
        )
        fig_domains.update_layout(
            xaxis_title='Email Count',
            yaxis_title='Domain',
            height=300
        )
        st.plotly_chart(fig_domains, use_container_width=True)
    
    with col4:
        # Email length analysis
        fig_lengths = go.Figure()
        fig_lengths.add_trace(go.Scatter(
            x=emails_df.index,
            y=emails_df['body_length'],
            mode='markers+lines',
            name='Email Body Length',
            line=dict(color='#007bff')
        ))
        fig_lengths.add_trace(go.Scatter(
            x=emails_df.index,
            y=emails_df['response_length'],
            mode='markers+lines',
            name='Response Length',
            line=dict(color='#28a745')
        ))
        fig_lengths.update_layout(
            title='Email and Response Length Analysis',
            xaxis_title='Email Index',
            yaxis_title='Character Count',
            height=300,
            hovermode='x unified'
        )
        st.plotly_chart(fig_lengths, use_container_width=True)


def display_email_statistics():
    """Display email count statistics with enhanced metrics."""
    unread_count, read_count = get_email_statistics()
    total_count = unread_count + read_count
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Support Emails",
            value=total_count,
            help="Total support emails in inbox"
        )
    
    with col2:
        st.metric(
            label="Unread Emails",
            value=unread_count,
            delta=f"{unread_count} pending" if unread_count > 0 else "All caught up",
            delta_color="normal" if unread_count == 0 else "inverse"
        )
    
    with col3:
        st.metric(
            label="Processed Emails", 
            value=read_count,
            help="Previously processed emails"
        )
    
    with col4:
        processing_rate = (read_count / total_count * 100) if total_count > 0 else 0
        st.metric(
            label="Processing Rate",
            value=f"{processing_rate:.1f}%",
            help="Percentage of emails processed"
        )
    
    st.markdown("---")
    
    # Charts section
    if total_count > 0:
        st.subheader("Email Overview Analytics")
        create_email_overview_charts(unread_count, read_count)


def display_processing_analytics(data: Dict[str, Any]) -> None:
    """Display comprehensive processing analytics."""
    st.subheader("Processing Session Analytics")
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Processed This Session",
            value=data['total_count'],
            help="Emails processed in current session"
        )
    
    with col2:
        st.metric(
            label="Urgent Priority",
            value=data['urgent_count'],
            delta="High Priority" if data['urgent_count'] > 0 else "No urgent emails",
            delta_color="inverse" if data['urgent_count'] > 0 else "normal"
        )
    
    with col3:
        negative_count = data['negative_sentiment_count']
        st.metric(
            label="Negative Sentiment",
            value=negative_count,
            delta="Needs attention" if negative_count > 0 else "No issues",
            delta_color="inverse" if negative_count > 0 else "normal"
        )
    
    with col4:
        positive_count = sum(1 for email in data['emails'] if email['sentiment'] == 'Positive')
        st.metric(
            label="Positive Sentiment",
            value=positive_count,
            delta="Happy customers" if positive_count > 0 else "",
            delta_color="normal"
        )
    
    with col5:
        avg_response_length = sum(len(email['draft_response']) for email in data['emails']) / len(data['emails']) if data['emails'] else 0
        st.metric(
            label="Avg Response Length",
            value=f"{avg_response_length:.0f}",
            help="Average characters in generated responses"
        )
    
    st.markdown("---")
    
    # Detailed analytics charts
    if data['total_count'] > 0:
        create_processing_analytics_charts(data)


def get_priority_class(priority: str) -> str:
    """Get CSS class for priority."""
    return "urgent-priority" if priority == "Urgent" else "normal-priority"


def get_sentiment_class(sentiment: str) -> str:
    """Get CSS class for sentiment."""
    if sentiment == "Positive":
        return "positive-sentiment"
    elif sentiment == "Negative":
        return "negative-sentiment"
    else:
        return "neutral-sentiment"


def get_status_badges(priority: str, sentiment: str) -> str:
    """Generate HTML status badges."""
    priority_class = "urgent-badge" if priority == "Urgent" else "normal-badge"
    
    if sentiment == "Positive":
        sentiment_class = "positive-badge"
    elif sentiment == "Negative":
        sentiment_class = "negative-badge"
    else:
        sentiment_class = "neutral-badge"
    
    return f"""
    <span class="status-badge {priority_class}">{priority}</span>
    <span class="status-badge {sentiment_class}">{sentiment}</span>
    """


def display_email_list(emails: List[Dict[str, Any]]) -> None:
    """Display list of processed emails with enhanced UI."""
    st.subheader("Processed Emails Detail")
    
    if not emails:
        st.info("No new unread emails to process. Click the button above to check again.")
        return
    
    # Filter options in sidebar
    with st.sidebar:
        st.subheader("Filter Options")
        
        # Priority filter
        priority_options = ["All"] + list(set(email['priority'] for email in emails))
        selected_priority = st.selectbox("Filter by Priority", priority_options)
        
        # Sentiment filter
        sentiment_options = ["All"] + list(set(email['sentiment'] for email in emails))
        selected_sentiment = st.selectbox("Filter by Sentiment", sentiment_options)
        
        # Apply filters
        filtered_emails = emails
        if selected_priority != "All":
            filtered_emails = [e for e in filtered_emails if e['priority'] == selected_priority]
        if selected_sentiment != "All":
            filtered_emails = [e for e in filtered_emails if e['sentiment'] == selected_sentiment]
        
        st.info(f"Showing {len(filtered_emails)} of {len(emails)} emails")
    
    # Display filtered emails
    for email in filtered_emails:
        # Create expander title with indicators
        priority_indicator = "URGENT" if email['priority'] == 'Urgent' else "NORMAL"
        sentiment_indicator = {"Positive": "POSITIVE", "Negative": "NEGATIVE", "Neutral": "NEUTRAL"}
        
        expander_title = f"[{priority_indicator}] {email['subject']}"
        
        # Apply CSS classes based on priority and sentiment
        priority_class = get_priority_class(email['priority'])
        sentiment_class = get_sentiment_class(email['sentiment'])
        
        with st.expander(expander_title, expanded=False):
            # Add custom styling
            st.markdown(f'<div class="{priority_class} {sentiment_class}" style="padding: 15px; border-radius: 8px; margin-bottom: 15px;">', unsafe_allow_html=True)
            
            # Email metadata with status badges
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**From:** {email['sender']}")
                st.write(f"**Date:** {email['date']}")
                st.write(f"**Summary:** {email['summary']}")
            
            with col2:
                # Status badges
                badges = get_status_badges(email['priority'], email['sentiment'])
                st.markdown(badges, unsafe_allow_html=True)
            
            if email['extracted_info']:
                st.write("**Extracted Information:**")
                st.json(email['extracted_info'])
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.divider()
            
            # AI-Generated Response Section
            st.write("**AI-Generated Draft Response:**")
            textarea_key = f"textarea_{email['id']}"
            edited_response = st.text_area(
                label="Edit the draft response:",
                value=email['draft_response'],
                height=150,
                key=textarea_key,
                help="Review and edit the AI-generated response before sending"
            )
            
            # Action buttons
            col1, col2, col3 = st.columns([2, 2, 6])
            
            with col1:
                if st.button("Send Email", key=f"send_{email['id']}", type="primary"):
                    with st.spinner("Sending email..."):
                        recipient = email['sender']
                        subject = email['subject']
                        success, message = send_email(recipient, subject, edited_response)
                        if success:
                            st.success("Email sent successfully: " + message)
                            st.balloons()
                        else:
                            st.error("Failed to send email: " + message)
            
            with col2:
                if st.button("Copy Response", key=f"copy_{email['id']}", type="secondary"):
                    st.code(edited_response, language=None)
                    st.info("Response copied to clipboard area above")
            
            # Original Email Section
            if st.checkbox("View Original Email", key=f"view_{email['id']}"):
                st.text_area(
                    label="Original email content:",
                    value=email['body'],
                    height=120,
                    disabled=True,
                    key=f"original_{email['id']}"
                )


def main():
    """Main application function."""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>AI Communication Assistant</h1>
        <p>Intelligently process and respond to customer support emails with comprehensive analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.radio(
            "Select View:",
            ["Dashboard", "Processing", "Analytics"],
            help="Navigate between different sections"
        )
    
    if page == "Dashboard":
        # Email Statistics Section
        st.subheader("Email Overview")
        display_email_statistics()
        
    elif page == "Processing":
        st.subheader("Email Processing")
        
        # Process Emails Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "Process New Unread Emails", 
                type="primary", 
                use_container_width=True,
                help="Fetch and analyze unread support emails"
            ):
                with st.spinner("Processing emails with AI..."):
                    data = call_backend()
                    if data:
                        st.session_state['email_data'] = data
                        if data['total_count'] > 0:
                            st.success(f"Successfully processed {data['total_count']} new emails!")
                            # Show quick stats
                            if data['urgent_count'] > 0:
                                st.warning(f"Warning: {data['urgent_count']} emails marked as urgent!")
                            if data['negative_sentiment_count'] > 0:
                                st.info(f"Info: {data['negative_sentiment_count']} emails need special attention (negative sentiment)")
                        else:
                            st.info("No new unread emails found. Great job staying on top of customer support!")
        
        st.markdown("---")

        # Display processed emails if available
        if 'email_data' in st.session_state and st.session_state['email_data']:
            data = st.session_state['email_data']
            
            # Only show processing results if there are emails to display
            if data['total_count'] > 0:
                display_email_list(data['emails'])
            else:
                st.info("No emails to process. All caught up!")
        else:
            # Welcome message
            st.markdown("""
            ### Welcome to AI Communication Assistant!
            
            This dashboard helps you:
            - **Monitor** your support email inbox
            - **Process** emails with AI analysis 
            - **Generate** intelligent draft responses
            - **Send** responses directly from the dashboard
            
            **Getting Started:**
            1. Check your email statistics in the Dashboard
            2. Click "Process New Unread Emails" to analyze unread messages
            3. Review AI-generated responses and send replies
            
            **Technical Requirements:**
            - Make sure your FastAPI backend is running on port 8000
            - Ensure Gmail credentials are configured in your environment
            """)
    
    else:  # Analytics page
        st.subheader("Advanced Analytics")
        
        if 'email_data' in st.session_state and st.session_state['email_data']:
            data = st.session_state['email_data']
            if data['total_count'] > 0:
                display_processing_analytics(data)
            else:
                st.info("No processing data available. Process some emails first.")
        else:
            st.info("No analytics data available. Please process some emails first to see detailed analytics.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; font-size: 12px; padding: 20px;">
        AI Communication Assistant Dashboard | Powered by Google Gemini & ChromaDB | Professional Edition
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()