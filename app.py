import streamlit as st
import time
from datetime import datetime
import threading

# Initialize session state variables
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Tab 1"
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if "counter" not in st.session_state:
    st.session_state.counter = 0
if "refresh_triggered" not in st.session_state:
    st.session_state.refresh_triggered = False


# Function to switch tabs
def switch_tab(tab_name):
    st.session_state.active_tab = tab_name
    # Reset the refresh trigger when switching to Tab 2
    if tab_name == "Tab 2":
        st.session_state.refresh_triggered = False


# Create tab buttons that act as tab selectors
col1, col2 = st.columns(2)
with col1:
    if st.button(
        "Tab 1",
        use_container_width=True,
        type="primary" if st.session_state.active_tab == "Tab 1" else "secondary",
    ):
        switch_tab("Tab 1")
with col2:
    if st.button(
        "Tab 2",
        use_container_width=True,
        type="primary" if st.session_state.active_tab == "Tab 2" else "secondary",
    ):
        switch_tab("Tab 2")

st.divider()


# Function to trigger refresh
def auto_refresh():
    # Only increment counter if we're on Tab 1
    if (
        st.session_state.active_tab == "Tab 1"
        and not st.session_state.refresh_triggered
    ):
        st.session_state.counter += 1
        st.session_state.last_refresh = datetime.now()
        st.session_state.refresh_triggered = True
        st.rerun()


# Tab 1 content
if st.session_state.active_tab == "Tab 1":
    st.title("Tab 1 - Auto-refreshing")
    st.write(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
    st.write(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    st.write(f"Refresh counter: {st.session_state.counter}")

    # Display some dynamic content
    st.subheader("Dynamic Content")
    st.write(f"Random value: {time.time()}")
    st.progress(datetime.now().second / 60)

    # Reset refresh trigger after displaying content
    st.session_state.refresh_triggered = False

    # Schedule the next refresh (only in Tab 1)
    time.sleep(0.1)  # Small delay to ensure UI renders

    # Use empty to place the auto-refresh trigger
    refresh_placeholder = st.empty()
    with refresh_placeholder:
        # Create invisible countdown for debugging
        countdown = 10
        if st.session_state.active_tab == "Tab 1":
            countdown_text = st.empty()
            countdown_text.caption(f"Next refresh in {countdown} seconds...")
            time.sleep(10)  # Wait 10 seconds
            auto_refresh()  # Trigger refresh

# Tab 2 content
elif st.session_state.active_tab == "Tab 2":
    st.title("Tab 2 - No auto-refresh")
    st.write(f"Current time: {datetime.now().strftime('%H:%M:%S')}")

    st.info("When you're in this tab, Tab 1 won't auto-refresh.")
    st.write("Return to Tab 1 to resume auto-refresh.")

    # Display some static content
    st.subheader("Static Content")
    st.write("This content doesn't change automatically.")
    st.write(f"Last refresh counter value: {st.session_state.counter}")
