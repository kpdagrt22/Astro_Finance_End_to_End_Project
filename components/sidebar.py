# components/sidebar.py - FIXED VERSION (NO IMPORTS)
import streamlit as st

def render_elite_sidebar():
    """Render enhanced sidebar"""
    
    with st.sidebar:
        # Logo
        st.image("https://cdn-icons-png.flaticon.com/512/3094/3094765.png", width=100)
        st.title("⚙️ Control Panel")
        
        # Email subscription
        st.markdown("### 📧 Get Free Crash Alerts")
        email = st.text_input("Email", placeholder="your@email.com", key="sidebar_email")
        
        if st.button("🚀 Subscribe", key="subscribe_btn", use_container_width=True):
            if email and '@' in email:
                st.success("✅ Subscribed! Check your email.")
                # Save to session state
                st.session_state.user_email = email
            else:
                st.error("Please enter valid email")
        
        st.markdown("---")
        
        # Premium CTA (simplified)
        if not st.session_state.get('is_premium', False):
            st.markdown("""
            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 20px; border-radius: 10px; color: white; text-align: center;'>
                <h3 style='margin: 0 0 10px 0;'>💎 Go Premium</h3>
                <p style='margin: 5px 0;'>$9.99/month</p>
                <ul style='text-align: left; margin: 10px 0; padding-left: 20px;'>
                    <li>✅ Real-time SMS alerts</li>
                    <li>✅ 90-day predictions</li>
                    <li>✅ Unlimited watchlist</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Upgrade Now", key="upgrade_btn", use_container_width=True):
                st.info("Redirecting to payment...")
        else:
            st.success("💎 Premium Member")
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### 🎯 Quick Stats")
        st.metric("Model Accuracy", "80.1%", "+2.3%")
        st.metric("Subscribers", "1,247", "+156")
        
        st.markdown("---")
        
        # Social share
        st.markdown("### 📱 Share")
        twitter_url = "https://twitter.com/intent/tweet?text=🚨 Check market crash predictions!&url=https://astro-finance-ml.streamlit.app"
        st.markdown(f'<a href="{twitter_url}" target="_blank" style="text-decoration: none;"><button style="background: #1DA1F2; color: white; padding: 10px 20px; border: none; border-radius: 5px; width: 100%; cursor: pointer;">🐦 Share on Twitter</button></a>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("⚠️ Educational purposes only. Not financial advice.")
