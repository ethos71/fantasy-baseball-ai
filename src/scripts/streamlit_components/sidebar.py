"""Sidebar controls and action buttons for Streamlit dashboard"""
import streamlit as st
import subprocess
import time

def render_sidebar_controls(selected_team):
    """Render sidebar team selector and action buttons"""
    
    # Yahoo Fantasy link
    st.sidebar.markdown(f"**Team:** {selected_team}")
    st.sidebar.markdown("[🔗 Open Yahoo Fantasy Baseball](https://baseball.fantasysports.yahoo.com)")
    
    # Action buttons
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Actions")
    
    render_rerun_button()
    render_waiver_button()
    render_refresh_button()
    render_calibrate_button()

def render_rerun_button():
    """Render rerun analysis button with progress tracking"""
    if st.sidebar.button("🔄 Rerun Analysis", help="Regenerate recommendations with current settings", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        output_expander = st.sidebar.expander("📋 Progress Log", expanded=True)
        
        process = subprocess.Popen(
            ["./fb-ai", "--date", "2025-09-28", "--quick"],
            cwd="/home/dominick/workspace/fantasy-baseball-ai",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        steps = [
            "Loading data...",
            "Running factor analyzers...",
            "Calculating scores...",
            "Generating recommendations...",
            "Finalizing..."
        ]
        
        output_lines = []
        step_idx = 0
        
        with output_expander:
            log_container = st.empty()
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line.strip())
                log_container.code('\n'.join(output_lines[-10:]))
                
                if "factor" in line.lower():
                    step_idx = min(1, step_idx)
                elif "score" in line.lower() or "weight" in line.lower():
                    step_idx = min(2, step_idx)
                elif "recommendation" in line.lower():
                    step_idx = min(3, step_idx)
                
                progress = min(0.9, (step_idx + 1) / len(steps))
                progress_bar.progress(progress)
                status_text.text(f"⏳ {steps[step_idx]}")
        
        returncode = process.wait()
        
        if returncode == 0:
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ Analysis complete! Refresh page to see results.")
        else:
            st.sidebar.error(f"❌ Error: Process exited with code {returncode}")

def render_waiver_button():
    """Render waiver wire button with progress tracking"""
    if st.sidebar.button("🔍 Waiver Wire", help="Run waiver wire prospect analysis", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        output_expander = st.sidebar.expander("📋 Progress Log", expanded=True)
        
        process = subprocess.Popen(
            ["python3", "src/scripts/daily_sitstart.py", "--date", "2025-09-28", "--skip-tune"],
            cwd="/home/dominick/workspace/fantasy-baseball-ai",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        progress = 0
        
        with output_expander:
            log_container = st.empty()
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line.strip())
                log_container.code('\n'.join(output_lines[-10:]))
                
                progress = min(0.9, progress + 0.05)
                progress_bar.progress(progress)
                
                if "waiver" in line.lower():
                    status_text.text("⏳ Analyzing waiver wire...")
                elif "player" in line.lower():
                    status_text.text("⏳ Evaluating players...")
        
        returncode = process.wait()
        
        if returncode == 0:
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ Waiver analysis complete! Check waiver wire section below.")
        else:
            st.sidebar.error(f"❌ Error: Process exited with code {returncode}")

def render_refresh_button():
    """Render refresh roster button with progress tracking"""
    if st.sidebar.button("📥 Refresh Roster", help="Fetch latest roster from Yahoo Fantasy", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        output_expander = st.sidebar.expander("📋 Progress Log", expanded=True)
        
        status_text.text("⏳ Connecting to Yahoo...")
        progress_bar.progress(0.1)
        
        process = subprocess.Popen(
            ["python3", "src/scripts/scrape/yahoo_scrape.py"],
            cwd="/home/dominick/workspace/fantasy-baseball-ai",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        progress = 0.1
        
        with output_expander:
            log_container = st.empty()
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line.strip())
                log_container.code('\n'.join(output_lines[-10:]))
                
                if "OAuth" in line or "authentication" in line.lower():
                    progress = 0.2
                    status_text.text("⏳ Authenticating...")
                elif "Finding" in line or "team" in line.lower():
                    progress = 0.4
                    status_text.text("⏳ Finding teams...")
                elif "Fetching" in line:
                    progress = min(0.8, progress + 0.2)
                    status_text.text("⏳ Fetching roster...")
                elif "Exported" in line:
                    progress = 0.95
                    status_text.text("⏳ Saving data...")
                
                progress_bar.progress(progress)
        
        returncode = process.wait()
        
        if returncode == 0:
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ Roster refreshed from Yahoo! Page will reload in 2 seconds...")
            time.sleep(2)
            st.rerun()
        else:
            st.sidebar.error(f"❌ Error refreshing roster")

def render_calibrate_button():
    """Render weight calibration button with progress tracking"""
    if st.sidebar.button("⚖️ Calibrate Weights", help="Run weight optimization (takes 30+ minutes)", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        output_expander = st.sidebar.expander("📋 Progress Log", expanded=True)
        
        status_text.text("⏳ Starting calibration...")
        progress_bar.progress(0.05)
        
        process = subprocess.Popen(
            ["python3", "src/scripts/daily_sitstart.py", "--date", "2025-09-28", "--tune-only"],
            cwd="/home/dominick/workspace/fantasy-baseball-ai",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        progress = 0.05
        trials_completed = 0
        
        with output_expander:
            log_container = st.empty()
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line.strip())
                log_container.code('\n'.join(output_lines[-15:]))
                
                if "trial" in line.lower() or "iteration" in line.lower():
                    trials_completed += 1
                    progress = min(0.9, 0.1 + (trials_completed / 100) * 0.8)
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ Optimizing weights... Trial {trials_completed}")
                elif "best" in line.lower() and "score" in line.lower():
                    status_text.text(f"⏳ Found better weights! Trial {trials_completed}")
        
        returncode = process.wait()
        
        if returncode == 0:
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ Weight calibration complete! Weights have been optimized.")
        else:
            st.sidebar.error(f"❌ Error during calibration")
