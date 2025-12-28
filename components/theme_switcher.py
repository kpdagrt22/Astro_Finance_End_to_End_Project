# components/theme_switcher.py
def theme_switcher():
    theme = st.sidebar.selectbox("🎨 Theme", ["Dark", "Light", "Cosmic"])
    
    if theme == "Dark":
        st.markdown("""
        <style>
        .stApp { background-color: #0e1117; color: white; }
        .stMetric > label { color: #aaa; }
        </style>
        """, unsafe_allow_html=True)
