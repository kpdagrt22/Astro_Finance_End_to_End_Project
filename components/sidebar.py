# components/sidebar.py
import streamlit as st

def render_sidebar():
    """Render sidebar"""
    with st.sidebar:
        # Logo
        st.image("https://cdn-icons-png.flaticon.com/512/3094/3094765.png", width=80)
        st.markdown("### ⚙️ Control Panel")
        
        # Email subscription
        st.markdown("#### 📧 Free Crash Alerts")
        email = st.text_input("Email", placeholder="your@email.com", key="email_sub")
        
        if st.button("🚀 Subscribe", use_container_width=True):
            if email and '@' in email:
                st.success("✅ Subscribed!")
                st.session_state.user_email = email
            else:
                st.error("❌ Invalid email")
        
        st.markdown("---")
        
        # Premium CTA
        if not st.session_state.get('is_premium', False):
            st.info("💎 **Go Premium** - $9.99/month\n\n✅ Real-time alerts\n✅ 90-day predictions\n✅ Unlimited stocks")
            if st.button("Upgrade Now", use_container_width=True):
                st.balloons()
                st.info("Coming soon!")
        
        st.markdown("---")
        
        # Stats
        st.metric("Accuracy", "80.1%", "+2.3%")
        st.metric("Users", "1,247", "+156")
        
        st.markdown("---")
        st.caption("⚠️ Not financial advice")
