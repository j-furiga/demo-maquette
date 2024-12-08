import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# Define threshold limits
TEMP_LIMIT = 80  # Celsius - typical max for industrial motors
VIB_ISO_LIMIT = 7.1  # mm/s - ISO 20816 Zone B/C boundary for medium machines
VIB_ML_LIMIT = 5.0  # mm/s - ML-based early warning threshold

# Generate fake time series data
def generate_fake_data():
    # One month of hourly data
    dates = pd.date_range(start='2023-01-01', end='2023-01-31', freq='H')
    
    # Temperature: Normal distribution with slight daily cycle
    temp_base = 45 + 5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24)
    temperature = temp_base + np.random.normal(0, 2, len(dates))
    
    # Vibration (ISO): Stable with small variations
    vib_iso_base = 4.5 * np.ones(len(dates))  # Constant base level
    vib_iso = vib_iso_base + np.random.normal(0, 0.3, len(dates))  # Small random variations
    vib_iso = np.clip(vib_iso, 3.5, 6.5)  # Keep within reasonable bounds
    
    # Vibration (ML): Normal until last 10 points where it goes above limit
    vib_ml_base = 3.8 * np.ones(len(dates))  # Normal base level
    vib_ml = vib_ml_base + np.random.normal(0, 0.25, len(dates))
    # Make last 10 points exceed the limit
    vib_ml[-10:] = VIB_ML_LIMIT + np.random.uniform(0.2, 0.8, 10)  # Above threshold
    # Clip all other points to normal range
    vib_ml[:-10] = np.clip(vib_ml[:-10], 3.0, 4.8)
    
    data = {
        'Date': dates,
        'Temperature (°C)': temperature,
        'Vibration ISO (mm/s)': vib_iso,
        'Vibration ML (mm/s)': vib_ml
    }
    return pd.DataFrame(data)

# Create pages
pages = ['Motor 1', 'Conveyor 1', 'Motor 2']
selected_page = st.sidebar.selectbox('Select Page', pages)

# Generate different data for each page
df = generate_fake_data()

# Layout for each page
def create_page_layout():
    # Temperature graph
    fig1 = px.line(df, x='Date', y='Temperature (°C)', 
                   title='Temperature Monitoring',
                   template='plotly_white')
    fig1.add_hline(y=TEMP_LIMIT, line_color="red", line_dash="dash", 
                   annotation_text="Temperature Limit (80°C)")
    fig1.update_layout(height=400)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("---")
    
    # Vibration ISO graph
    fig2 = px.line(df, x='Date', y='Vibration ISO (mm/s)', 
                   title='Vibration Monitoring (ISO 20816)',
                   template='plotly_white')
    fig2.add_hline(y=VIB_ISO_LIMIT, line_color="red", line_dash="dash", 
                   annotation_text="ISO Limit (7.1 mm/s)")
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # Vibration ML graph with alarm condition
    fig3 = px.line(df, x='Date', y='Vibration ML (mm/s)', 
                   title='Vibration Monitoring (Machine Learning)',
                   template='plotly_white')
    
    # Color the line based on threshold
    df['Above_Threshold'] = df['Vibration ML (mm/s)'] > VIB_ML_LIMIT
    
    # Plot normal values in blue
    mask_normal = ~df['Above_Threshold']
    fig3.add_scatter(x=df[mask_normal]['Date'], 
                     y=df[mask_normal]['Vibration ML (mm/s)'],
                     mode='lines',
                     line=dict(color='blue'),
                     showlegend=False)
    
    # Plot above-threshold values in red
    mask_alarm = df['Above_Threshold']
    fig3.add_scatter(x=df[mask_alarm]['Date'], 
                     y=df[mask_alarm]['Vibration ML (mm/s)'],
                     mode='lines',
                     line=dict(color='red', width=3),
                     showlegend=False)
    
    fig3.add_hline(y=VIB_ML_LIMIT, line_color="red", line_dash="dash", 
                   annotation_text="ML Threshold (5.0 mm/s)")
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)
    
    # Add alarm indicator if any recent points are above threshold
    if df['Above_Threshold'].iloc[-10:].any():
        st.error("⚠️ ALARM: ML Vibration levels exceeding threshold! ⚠️")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Current Vibration", 
                f"{df['Vibration ML (mm/s)'].iloc[-1]:.2f} mm/s",
                f"{df['Vibration ML (mm/s)'].iloc[-1] - VIB_ML_LIMIT:.2f} mm/s above limit",
                delta_color="inverse"
            )
        with col2:
            st.metric(
                "Time in Alarm", 
                f"{df['Above_Threshold'].iloc[-10:].sum()} hours",
                "Critical condition"
            )

    # Single button at the bottom of the page
    st.button(f'Analyze {selected_page}', key=f'btn_{selected_page}')

# Display selected page
st.title(selected_page)
create_page_layout() 