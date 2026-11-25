import streamlit as st
# in the app.py
page = st.navigation(
    [
        st.Page("views/single_phase_three_phase.py", title="Calculate for 1 Phase, 3 Phase", icon="1️⃣"),
        st.Page("views/calculate_ct.py", title="Calculate for CT", icon="3️⃣"),
        st.Page("views/about.py", title="About", icon="ℹ️"),
    ]
)
page.run()