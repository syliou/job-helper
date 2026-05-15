"""Simple Streamlit interface for the resume optimization helper."""

import streamlit as st

from job_helper import (
    analyze_job_text,
    load_analysis_config,
    prepare_resume_context,
    read_resume_pdf_stream,
)


@st.cache_data
def cached_analysis_config():
    """Load rule files once per Streamlit session."""
    return load_analysis_config()


def read_uploaded_job_file(uploaded_file):
    """Read a text job description uploaded through Streamlit."""
    if uploaded_file is None:
        return ""

    try:
        return uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        return uploaded_file.getvalue().decode("utf-8", errors="replace")


def run_analysis(resume_file, pasted_job_text, uploaded_job_file):
    """Run the existing analysis logic from job_helper.py."""
    resume_text = read_resume_pdf_stream(resume_file)
    job_text_from_file = read_uploaded_job_file(uploaded_job_file)
    job_text = pasted_job_text.strip() or job_text_from_file.strip()

    if not resume_text:
        raise ValueError("No extractable text was found in the resume PDF.")
    if not job_text:
        raise ValueError("Please paste a job description or upload a .txt job description file.")

    config = cached_analysis_config()
    resume_context = prepare_resume_context(
        resume_text,
        config["normal_keywords"],
        config["critical_keywords"],
        config["synonyms"],
    )

    job_name = uploaded_job_file.name if uploaded_job_file else "pasted_job_description.txt"
    return analyze_job_text(
        job_name,
        job_text,
        resume_text,
        resume_context["sections"],
        resume_context["bullets"],
        config["normal_keywords"],
        config["critical_keywords"],
        resume_context["resume_normal"],
        resume_context["resume_critical"],
        resume_context["resume_match_details"],
        resume_context["keyword_sections"],
        config["synonyms"],
        config["role_profiles"],
    )


def main():
    """Render the Streamlit app."""
    st.set_page_config(page_title="Resume Optimization Helper", layout="wide")

    st.title("Resume Optimization Helper")
    st.write("Upload a resume PDF, add a job description, and generate the same review report locally.")

    resume_file = st.file_uploader("Resume PDF", type=["pdf"])
    uploaded_job_file = st.file_uploader("Optional job description .txt file", type=["txt"])
    pasted_job_text = st.text_area(
        "Job description text",
        height=280,
        placeholder="Paste the job description here. If you also upload a .txt file, pasted text will be used first.",
    )

    analyze_clicked = st.button("Analyze", type="primary")

    if analyze_clicked:
        if resume_file is None:
            st.error("Please upload a resume PDF.")
            return

        try:
            with st.spinner("Analyzing resume and job description..."):
                analysis = run_analysis(resume_file, pasted_job_text, uploaded_job_file)
        except Exception as error:
            st.error(str(error))
            return

        report = analysis["markdown_report"]
        report_data = analysis["report_data"]

        st.success(
            f"Analysis complete: {report_data['fit_category']} "
            f"({report_data['fit_score']}%)"
        )
        st.markdown(report)
        st.download_button(
            "Download markdown report",
            data=report,
            file_name="resume_job_review.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
