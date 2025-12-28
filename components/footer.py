# components/footer.py
import streamlit as st

def render_footer():
    """Render footer"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: #666;'>
        <p style='margin: 10px 0;'>
            <b>🌙 Astro Finance ML</b> | 
            <a href='#'>Privacy</a> | 
            <a href='#'>Terms</a> | 
            <a href='#'>API</a>
        </p>
        <p style='font-size: 0.9rem; margin: 10px 0;'>
            Made with ❤️ combining celestial wisdom with AI
        </p>
        <p style='font-size: 0.8rem; color: #999;'>
            © 2025 Astro Finance ML. Educational purposes only.
        </p>
    </div>
    """, unsafe_allow_html=True)
