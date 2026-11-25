import streamlit as st

page = st.navigation(
    [
        st.Page("pages/single_phase_three_phase.py", title="Calculate for 1 Phase, 3 Phase", icon="1️⃣"),
        st.Page("pages/calculate_ct.py", title="Calculate for CT", icon="3️⃣"),
        st.Page("pages/about.py", title="About", icon="ℹ️"),
    ]
)
page.run()