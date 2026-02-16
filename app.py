import streamlit as st
import pandas as pd
import time
import json
import os
import subprocess
import signal
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=True)

# Configuration paths
BASE_DIR = Path(__file__).parent
PROGRESS_FILE = BASE_DIR / "progress.json"
LOG_FILE = BASE_DIR / "enrichment.log"
PID_FILE = BASE_DIR / ".enrichment_service.pid"
UPLOADED_CSV = BASE_DIR / "uploaded_companies.csv"

st.set_page_config(
    page_title="EnrichIQ - Company Data Enrichment",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# === Service Management Functions ===

def is_service_running() -> bool:
    """Check if the enrichment service is running."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, OSError, ProcessLookupError):
        PID_FILE.unlink(missing_ok=True)
        return False


def start_service(options: dict = None) -> tuple[bool, str]:
    """Start the enrichment service as a background process."""
    if is_service_running():
        return False, "Service is already running"

    try:
        cmd = ["python", str(BASE_DIR / "enrichment_service.py")]

        if options:
            if options.get("emails_only"):
                cmd.append("--emails-only")
            if options.get("phones_only"):
                cmd.append("--phones-only")
            if options.get("websites_only"):
                cmd.append("--websites-only")
            if options.get("reset"):
                cmd.append("--reset")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=str(BASE_DIR)
        )

        PID_FILE.write_text(str(process.pid))
        return True, f"Enrichment started"
    except Exception as e:
        return False, f"Failed to start: {e}"


def stop_service() -> tuple[bool, str]:
    """Stop the running enrichment service."""
    if not PID_FILE.exists():
        return False, "Service is not running"

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)
        return True, "Service stopped"
    except ProcessLookupError:
        PID_FILE.unlink(missing_ok=True)
        return False, "Service was not running"
    except Exception as e:
        return False, f"Failed to stop: {e}"


def get_progress() -> dict:
    """Load progress data from progress.json."""
    if not PROGRESS_FILE.exists():
        return None
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_recent_logs(num_lines: int = 15) -> list[str]:
    """Get the most recent log entries."""
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            return lines[-num_lines:]
    except IOError:
        return []


def get_output_file() -> Path:
    """Get the date-based output file path."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return BASE_DIR / f"{date_str} - Companies Enriched.csv"


def format_timestamp(iso_str: str) -> str:
    """Format ISO timestamp to readable format."""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return iso_str


def get_current_step() -> int:
    """Determine current step based on app state."""
    service_running = is_service_running()
    has_file = UPLOADED_CSV.exists()
    output_file = get_output_file()
    has_output = output_file.exists()
    progress = get_progress()

    if service_running:
        return 3  # Progress
    elif has_output and progress:
        # Check if enrichment was completed recently
        stats = progress.get("stats", {})
        total_processed = (
            stats.get("emails_found", 0) + stats.get("emails_not_found", 0) +
            stats.get("phones_found", 0) + stats.get("phones_not_found", 0) +
            stats.get("websites_found", 0) + stats.get("websites_not_found", 0)
        )
        if total_processed > 0:
            return 4  # Download
    elif has_file:
        return 2  # Choose enrichment
    return 1  # Upload


def main():
    # === Global Styles ===
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 900px;
    }

    /* Step indicator */
    .step-indicator {
        display: flex;
        justify-content: center;
        gap: 0;
        margin: 20px 0 30px 0;
    }
    .step {
        display: flex;
        align-items: center;
        padding: 8px 16px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .step-number {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 8px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .step-active .step-number {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    .step-active .step-label {
        color: #667eea;
        font-weight: 600;
    }
    .step-completed .step-number {
        background: #10b981;
        color: white;
    }
    .step-completed .step-label {
        color: #10b981;
    }
    .step-inactive .step-number {
        background: #e5e7eb;
        color: #9ca3af;
    }
    .step-inactive .step-label {
        color: #9ca3af;
    }
    .step-connector {
        width: 40px;
        height: 2px;
        background: #e5e7eb;
        margin: 0 5px;
        align-self: center;
    }
    .step-connector-active {
        background: #10b981;
    }

    /* Section styling */
    .section-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .section-card-active {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    .section-card-inactive {
        opacity: 0.5;
        pointer-events: none;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Enrichment cards */
    .enrich-card {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
        height: 100%;
    }
    .enrich-card:hover {
        border-color: #667eea;
        background: #f0f4ff;
        transform: translateY(-2px);
    }
    .enrich-icon {
        font-size: 2rem;
        margin-bottom: 8px;
    }
    .enrich-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 4px;
    }
    .enrich-desc {
        font-size: 0.8rem;
        color: #6b7280;
        margin-bottom: 12px;
    }

    /* Progress section */
    .activity-log {
        background: #1f2937;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 0.75rem;
        color: #10b981;
        max-height: 200px;
        overflow-y: auto;
    }
    .activity-line {
        margin: 2px 0;
    }
    .activity-line-error {
        color: #ef4444;
    }

    /* Download section */
    .download-card {
        background: linear-gradient(135deg, #ecfdf5, #d1fae5);
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    </style>
    """, unsafe_allow_html=True)

    # === Header ===
    st.markdown("""
    <div style="text-align: center; margin-bottom: 10px;">
        <h1 style="font-size: 2.2rem; font-weight: 700; margin-bottom: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🧠 EnrichIQ
        </h1>
        <p style="font-size: 0.9rem; color: #666; margin: 5px 0;">Company data enrichment platform</p>
    </div>
    """, unsafe_allow_html=True)

    # === Determine Current State ===
    current_step = get_current_step()
    service_running = is_service_running()
    has_file = UPLOADED_CSV.exists()
    progress_data = get_progress()
    output_file = get_output_file()

    # === Step Indicator ===
    def step_class(step_num):
        if step_num < current_step:
            return "step-completed"
        elif step_num == current_step:
            return "step-active"
        return "step-inactive"

    def connector_class(step_num):
        if step_num < current_step:
            return "step-connector step-connector-active"
        return "step-connector"

    st.markdown(f"""
    <div class="step-indicator">
        <div class="step {step_class(1)}">
            <div class="step-number">{'✓' if current_step > 1 else '1'}</div>
            <span class="step-label">Upload</span>
        </div>
        <div class="{connector_class(1)}"></div>
        <div class="step {step_class(2)}">
            <div class="step-number">{'✓' if current_step > 2 else '2'}</div>
            <span class="step-label">Enrich</span>
        </div>
        <div class="{connector_class(2)}"></div>
        <div class="step {step_class(3)}">
            <div class="step-number">{'✓' if current_step > 3 else '3'}</div>
            <span class="step-label">Progress</span>
        </div>
        <div class="{connector_class(3)}"></div>
        <div class="step {step_class(4)}">
            <div class="step-number">4</div>
            <span class="step-label">Download</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # === STEP 1: Upload ===
    with st.container():
        is_active = current_step == 1
        st.markdown(f'<div class="section-title">{"📁" if is_active else "✅"} Step 1: Upload Company List</div>', unsafe_allow_html=True)

        if current_step == 1:
            col1, col2 = st.columns([2, 1])

            with col1:
                uploaded_file = st.file_uploader(
                    "Upload CSV file",
                    type=['csv'],
                    key="csv_uploader",
                    help="CSV file with company data"
                )

            with col2:
                st.markdown("""
                <div style="padding: 12px; background: #f0f7ff; border-radius: 8px; border-left: 3px solid #667eea; margin-top: 10px;">
                    <p style="margin: 0; font-size: 0.85rem; color: #374151;"><strong>Required:</strong> "Name" column</p>
                    <p style="margin: 6px 0 0 0; font-size: 0.8rem; color: #6b7280;">Optional: City, Website</p>
                </div>
                """, unsafe_allow_html=True)

            if uploaded_file is not None:
                try:
                    uploaded_df = pd.read_csv(uploaded_file)
                    col_mapping = {col: col.strip().lower() for col in uploaded_df.columns}

                    company_col = None
                    for col, normalized in col_mapping.items():
                        if normalized in ['company name', 'name']:
                            company_col = col
                            break

                    if company_col is None:
                        st.error(f"❌ CSV must have 'Name' column. Found: {', '.join(uploaded_df.columns.tolist())}")
                    else:
                        company_names = uploaded_df[company_col].dropna().astype(str).str.strip()
                        company_names = company_names[company_names != ''].tolist()

                        if company_names:
                            # Find optional columns
                            city_col = None
                            website_col = None
                            for col, normalized in col_mapping.items():
                                if normalized == 'city':
                                    city_col = col
                                if normalized == 'website':
                                    website_col = col

                            # Build service DataFrame
                            service_df = pd.DataFrame({
                                'Name': company_names,
                                'City': uploaded_df[city_col].fillna('').astype(str).tolist()[:len(company_names)] if city_col else [''] * len(company_names),
                                'Website': uploaded_df[website_col].fillna('').astype(str).tolist()[:len(company_names)] if website_col else [''] * len(company_names),
                                'Email': [''] * len(company_names),
                                'Phone': [''] * len(company_names)
                            })
                            service_df.to_csv(UPLOADED_CSV, index=False)

                            # Clear old progress
                            if PROGRESS_FILE.exists():
                                PROGRESS_FILE.unlink()

                            st.success(f"✅ Loaded {len(company_names)} companies")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ No company names found")
                except Exception as e:
                    st.error(f"❌ Error reading CSV: {str(e)}")

        elif has_file:
            # Show summary of uploaded file
            try:
                df = pd.read_csv(UPLOADED_CSV)
                st.markdown(f"""
                <div style="padding: 10px 15px; background: #ecfdf5; border-radius: 8px; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.2rem;">📄</span>
                    <span style="color: #065f46; font-weight: 500;">{len(df)} companies loaded</span>
                    <span style="color: #6b7280; font-size: 0.85rem;">({UPLOADED_CSV.name})</span>
                </div>
                """, unsafe_allow_html=True)

                # Compact preview
                with st.expander("Preview data", expanded=False):
                    st.dataframe(df.head(5), use_container_width=True, hide_index=True)

                if st.button("Upload New File", key="new_upload"):
                    UPLOADED_CSV.unlink(missing_ok=True)
                    if PROGRESS_FILE.exists():
                        PROGRESS_FILE.unlink()
                    st.rerun()
            except:
                pass

    st.markdown("---")

    # === STEP 2: Choose Enrichment ===
    with st.container():
        is_active = current_step == 2
        is_disabled = current_step < 2 or service_running

        st.markdown(f'<div class="section-title">{"🎯" if is_active else "○"} Step 2: Choose Enrichment Type</div>', unsafe_allow_html=True)

        if is_disabled and current_step < 2:
            st.markdown('<p style="color: #9ca3af; font-style: italic;">Upload a file first to enable enrichment options</p>', unsafe_allow_html=True)
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("""
                <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 10px; border: 2px solid #e2e8f0;">
                    <div style="font-size: 2rem;">📧</div>
                    <div style="font-size: 1rem; font-weight: 600; color: #1f2937;">Emails</div>
                    <div style="font-size: 0.8rem; color: #6b7280; margin: 5px 0 10px 0;">Find contact emails from company websites</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Start Email Enrichment", key="btn_emails", disabled=is_disabled, use_container_width=True):
                    success, msg = start_service({'emails_only': True})
                    if success:
                        st.rerun()
                    else:
                        st.error(msg)

            with col2:
                st.markdown("""
                <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 10px; border: 2px solid #e2e8f0;">
                    <div style="font-size: 2rem;">🌐</div>
                    <div style="font-size: 1rem; font-weight: 600; color: #1f2937;">Websites</div>
                    <div style="font-size: 0.8rem; color: #6b7280; margin: 5px 0 10px 0;">Find company websites via Google search</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Start Website Enrichment", key="btn_websites", disabled=is_disabled, use_container_width=True):
                    success, msg = start_service({'websites_only': True})
                    if success:
                        st.rerun()
                    else:
                        st.error(msg)

            with col3:
                st.markdown("""
                <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 10px; border: 2px solid #e2e8f0;">
                    <div style="font-size: 2rem;">📞</div>
                    <div style="font-size: 1rem; font-weight: 600; color: #1f2937;">Phones</div>
                    <div style="font-size: 0.8rem; color: #6b7280; margin: 5px 0 10px 0;">Find Dutch phone numbers from websites</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Start Phone Enrichment", key="btn_phones", disabled=is_disabled, use_container_width=True):
                    success, msg = start_service({'phones_only': True})
                    if success:
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown("---")

    # === STEP 3: Progress ===
    with st.container():
        is_active = current_step == 3 or service_running

        st.markdown(f'<div class="section-title">{"⚙️" if is_active else "○"} Step 3: Enrichment Progress</div>', unsafe_allow_html=True)

        if service_running:
            # Stop button
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🛑 Stop", key="stop_btn", use_container_width=True):
                    stop_service()
                    st.rerun()

            # Progress stats
            if progress_data:
                stats = progress_data.get("stats", {})

                emails_found = stats.get("emails_found", 0)
                emails_not_found = stats.get("emails_not_found", 0)
                websites_found = stats.get("websites_found", 0)
                websites_not_found = stats.get("websites_not_found", 0)
                phones_found = stats.get("phones_found", 0)
                phones_not_found = stats.get("phones_not_found", 0)

                total_found = emails_found + websites_found + phones_found
                total_not_found = emails_not_found + websites_not_found + phones_not_found
                total = total_found + total_not_found

                # Get total companies
                try:
                    df = pd.read_csv(UPLOADED_CSV)
                    total_companies = len(df)
                except:
                    total_companies = total if total > 0 else 100

                progress_pct = min(total / total_companies, 1.0) if total_companies > 0 else 0

                st.progress(progress_pct)
                st.markdown(f"**{total}/{total_companies}** companies processed ({progress_pct*100:.0f}%)")

                # Stats row
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                with stat_col1:
                    st.metric("Found", total_found, delta=None)
                with stat_col2:
                    st.metric("Not Found", total_not_found, delta=None)
                with stat_col3:
                    success_rate = (total_found / total * 100) if total > 0 else 0
                    st.metric("Success Rate", f"{success_rate:.0f}%")

            # Activity log
            st.markdown("**Live Activity:**")
            log_lines = get_recent_logs(12)
            if log_lines:
                log_html = ""
                for line in log_lines:
                    line = line.strip()
                    if "ERROR" in line:
                        log_html += f'<div class="activity-line activity-line-error">{line}</div>'
                    else:
                        log_html += f'<div class="activity-line">{line}</div>'
                st.markdown(f'<div class="activity-log">{log_html}</div>', unsafe_allow_html=True)
            else:
                st.info("Starting enrichment...")

        elif current_step < 3:
            st.markdown('<p style="color: #9ca3af; font-style: italic;">Start an enrichment to see progress</p>', unsafe_allow_html=True)

        elif progress_data:
            # Show completed progress summary
            stats = progress_data.get("stats", {})
            total_found = stats.get("emails_found", 0) + stats.get("websites_found", 0) + stats.get("phones_found", 0)
            total_not_found = stats.get("emails_not_found", 0) + stats.get("websites_not_found", 0) + stats.get("phones_not_found", 0)

            st.markdown(f"""
            <div style="padding: 12px; background: #ecfdf5; border-radius: 8px; border-left: 3px solid #10b981;">
                <p style="margin: 0; color: #065f46;">✅ <strong>Enrichment completed</strong> - {total_found} found, {total_not_found} not found</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # === STEP 4: Download ===
    with st.container():
        is_active = current_step == 4

        st.markdown(f'<div class="section-title">{"📥" if is_active else "○"} Step 4: Download Results</div>', unsafe_allow_html=True)

        if output_file.exists() and progress_data:
            stats = progress_data.get("stats", {})
            total_found = stats.get("emails_found", 0) + stats.get("websites_found", 0) + stats.get("phones_found", 0)
            total_not_found = stats.get("emails_not_found", 0) + stats.get("websites_not_found", 0) + stats.get("phones_not_found", 0)
            total = total_found + total_not_found
            success_rate = (total_found / total * 100) if total > 0 else 0

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ecfdf5, #d1fae5); border: 2px solid #10b981; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">✅</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #065f46; margin-bottom: 5px;">Enrichment Complete!</div>
                <div style="font-size: 0.9rem; color: #047857; margin-bottom: 15px;">
                    {total} companies processed • {total_found} enriched • {success_rate:.0f}% success rate
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Download button
            try:
                with open(output_file, 'r') as f:
                    csv_data = f.read()

                st.download_button(
                    label=f"📥 Download {output_file.name}",
                    data=csv_data,
                    file_name=output_file.name,
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error reading output file: {e}")

            # Preview with combined email view
            with st.expander("Preview results", expanded=False):
                try:
                    result_df = pd.read_csv(output_file)

                    # Create combined Email column for display
                    def format_email(row):
                        email = row.get('Email', '')
                        probable = row.get('Probable_Email', '')

                        if email and email.strip():
                            return f"✓ {email}"
                        elif probable and probable.strip():
                            return f"📧 {probable} (suggested)"
                        else:
                            return "—"

                    # Create display dataframe with combined view
                    display_df = result_df.copy()
                    display_df['Email_Display'] = display_df.apply(format_email, axis=1)

                    # Select columns for display (hide separate Probable_Email)
                    display_cols = ['Name', 'City', 'Website', 'Email_Display', 'Phone']
                    display_cols = [c for c in display_cols if c in display_df.columns or c == 'Email_Display']

                    # Rename for display
                    display_df = display_df[display_cols].rename(columns={'Email_Display': 'Email'})

                    st.dataframe(display_df.head(10), use_container_width=True, hide_index=True)

                    # Stats
                    verified = len(result_df[result_df['Email'].notna() & (result_df['Email'] != '')])
                    suggested = len(result_df[(result_df['Email'].isna() | (result_df['Email'] == '')) &
                                              result_df['Probable_Email'].notna() & (result_df['Probable_Email'] != '')])
                    no_email = len(result_df) - verified - suggested

                    st.markdown(f"""
                    <div style="display: flex; gap: 15px; margin-top: 10px; font-size: 0.85rem;">
                        <span style="color: #10b981;">✓ {verified} verified</span>
                        <span style="color: #f59e0b;">📧 {suggested} suggested</span>
                        <span style="color: #9ca3af;">— {no_email} no email</span>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading preview: {e}")

            # Start new
            if st.button("🔄 Start New Enrichment", key="new_enrichment"):
                if PROGRESS_FILE.exists():
                    PROGRESS_FILE.unlink()
                st.rerun()

        elif current_step < 4:
            st.markdown('<p style="color: #9ca3af; font-style: italic;">Complete an enrichment to download results</p>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; padding: 15px; border-top: 1px solid #e5e7eb;">
        <p style="font-size: 0.8rem; color: #9ca3af;">
            Powered by <a href="http://brightdata.com/" target="_blank" style="color: #667eea; text-decoration: none;">Bright Data</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh while service is running (at the END after all content rendered)
    if service_running:
        time.sleep(2)  # Wait 2 seconds before refresh
        st.rerun()


if __name__ == "__main__":
    main()
