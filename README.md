# Job Application Helper

This is a beginner-friendly Python project that helps you review a job application.

You can use it in two ways:

- Run a simple local Streamlit app where you upload a resume PDF and paste or upload one job description.
- Run the original batch script that reads files from the `data/` folder.

The batch script reads:

- `data/base_resume.pdf`
- `data/target_keywords.txt`
- `data/critical_keywords.txt`
- `data/synonyms.json`
- `data/job_role_profiles.json`
- All `.txt` files inside `data/jobs/`

Then it creates:

- One report for each job inside `outputs/`
- One summary CSV file at `outputs/job_summary.csv`

The Streamlit app displays the report directly in your browser and provides a Markdown download button.

## What It Does

The script will:

1. Read all `.txt` job description files inside `data/jobs/`.
2. Read your base resume from `data/base_resume.pdf` using `pypdf`.
3. Load the target keyword list from `data/target_keywords.txt`.
4. Load high-priority keywords from `data/critical_keywords.txt`.
5. Find critical and normal keywords in each job description and in your resume.
6. Use `data/synonyms.json` for lightweight semantic matching.
7. Detect the likely role family from `data/job_role_profiles.json`.
8. Give critical keywords higher scoring weight.
9. Adjust review priorities based on the detected role family.
10. Analyze relevant resume bullets, industry tone, qualitative ATS readability, role-specific gaps, and tailoring priorities.
11. Classify the job as `Strong fit`, `Moderate fit`, or `Weak fit`.
12. Recommend whether to apply, tailor the resume first, or make the job low priority.
13. Save a separate report for each job in `outputs/`.
14. Save a summary CSV at `outputs/job_summary.csv`.
15. Show a clear warning if the resume PDF has no extractable text.

## Project Structure

```text
data/
  base_resume.pdf
  target_keywords.txt
  critical_keywords.txt
  synonyms.json
  job_role_profiles.json
  jobs/
    sample_job.txt
outputs/
  one report per job
  job_summary.csv
app.py
job_helper.py
README.md
requirements.txt
```

## Windows PowerShell Setup

Open Windows PowerShell in this project folder:

```powershell
cd "C:\Users\paula\OneDrive\Desktop\Taiwan\#Python\us_job_helper"
```

Install the required packages:

```powershell
python -m pip install -r requirements.txt
```

## How To Use The Streamlit App

Start the local app:

```powershell
python -m streamlit run app.py
```

Then use the browser page that opens:

1. Upload your resume PDF.
2. Paste the job description into the text box, or upload a `.txt` job description file.
3. Click `Analyze`.
4. Read the generated report in the app.
5. Use `Download markdown report` if you want to save the report.

The app does not require placing your resume or job description inside the `data/` folder. It still reuses the same rule files:

- `data/target_keywords.txt`
- `data/critical_keywords.txt`
- `data/synonyms.json`
- `data/job_role_profiles.json`

## How To Use The Batch Script

1. Put your resume PDF in the `data` folder.
2. Rename it exactly:

```text
base_resume.pdf
```

3. Create one `.txt` file for each job inside `data/jobs/`.
4. Paste one job description into each job file.
5. Review `data/target_keywords.txt` and edit it if you want different normal keywords.
6. Review `data/critical_keywords.txt` and edit it if you want different high-priority keywords.
7. Review `data/synonyms.json` if you want to add semantic keyword relationships.
8. Use simple job file names, such as:

- `data/jobs/python_developer.txt`
- `data/jobs/data_analyst.txt`
- `data/jobs/customer_support.txt`

9. Run the script:

```powershell
python job_helper.py
```

10. Open the matching reports in `outputs/`.
11. Open `outputs/job_summary.csv` to compare all jobs in one table.

For example:

- `data/jobs/python_developer.txt` creates `outputs/python_developer_review.md`
- `data/jobs/data_analyst.txt` creates `outputs/data_analyst_review.md`

The summary CSV includes:

- `job_file`
- `job_type`
- `fit_category`
- `match_rate`
- `matched_keywords`
- `missing_keywords`
- `recommendation`
- `report_file`

## Target Keywords

The main comparison uses `data/target_keywords.txt` and `data/critical_keywords.txt`.

Add one keyword or phrase per line. Normal keywords go in `data/target_keywords.txt`, for example:

```text
water treatment
UPW
ozone
reaction kinetics
data interpretation
```

If `data/target_keywords.txt` does not exist, the script creates a default version with water treatment and UPW-related keywords.

Critical keywords go in `data/critical_keywords.txt`, for example:

```text
UPW
reverse osmosis
semiconductor
pilot testing
process optimization
```

Critical keywords count more heavily in the fit score and are shown separately in each report.

## Semantic Matching

The script uses `data/synonyms.json` for lightweight semantic matching.

This helps partial matches such as:

- `process optimization` matching wording like `optimized reaction conditions`
- `data analysis` matching wording like `interpreted water chemistry datasets`
- `pilot testing` matching wording like `laboratory-scale evaluation`

The logic is intentionally simple:

- exact phrase match gets full credit
- synonym phrase match gets partial credit
- token overlap gets partial credit when most important words overlap

No large machine learning models are used.

## Job Type Detection

The script uses simple keyword patterns in `data/job_role_profiles.json` to classify each job description into a role family.

Current role families include:

- `Water Treatment Engineer`
- `Wastewater Treatment Engineer`
- `Process Engineer`
- `Environmental Engineer`
- `Environmental Consultant`
- `UPW Engineer`
- `Industrial Water Engineer`
- `R&D Engineer/Scientist (Water)`

Each role profile defines:

- priority skills
- preferred language style
- acceptable academic level
- transferable engineering skills
- operational/process emphasis
- reporting/consulting emphasis

The detected role family adjusts the review priorities:

- UPW roles reward semiconductor, high-purity water, and treatment chemistry relevance.
- Process engineering roles reward troubleshooting, operations, equipment, and optimization language.
- Consulting roles reward reporting, communication, client/project wording, and recommendations.
- Water R&D roles tolerate more academic depth when tied to applied treatment outcomes.

The score and recommendation also use role-specific priority checks. For example, a consulting role gets extra credit for project/reporting language, while a process role is checked for optimization, operations, equipment, troubleshooting, and process-control wording.

The final fit score also includes a separate domain alignment score. Water, wastewater, environmental engineering, UPW, industrial water, treatment chemistry, contaminant control, advanced oxidation, and water quality overlap are weighted heavily. General transferable engineering skills can improve a fit, but they should not outweigh a weak domain match.

## Helpful Error Messages

If `data/base_resume.pdf` is missing, the script tells you exactly where to put it.

If the PDF has no extractable text, the script shows a warning. This can happen when a resume is scanned or image-only.

## Report Sections

Each Markdown report includes:

- Overall Fit Assessment
- Role-Specific Gaps
- Strategic Resume Positioning
- Resume Bullet Relevance Analysis
- Tailored Professional Summary Suggestion
- Resume Tailoring Priorities
- Recommended Resume Focus

The overall assessment includes a short ATS readability line instead of detailed readability metrics.

The role-specific gaps section scans the job description for concrete requirements that may not be in the controlled keyword files, such as BioWin/GPSX/Sumo, P&ID, MOC, cost estimates, plans/specifications, hydraulics, plant operations, safety compliance, and regulatory or agency reporting.

The strategic positioning section identifies the strongest positioning angle, technical strengths to emphasize, experience that may be too academic or detailed, and a realistic engineering identity for the specific job.

Each report also includes a 2-4 sentence professional summary suggestion tailored to the detected job type. It is based only on resume-supported experience and is written in a US industry resume tone.

The bullet relevance section classifies bullets as direct matches, transferable matches, or low relevance. Transferable matching uses simple rule tables, not machine learning.

## Fit Scoring

The fit score is weighted:

- Critical keywords count more than normal keywords.
- Exact matches count more than synonym or token-overlap matches.
- Keywords found in Experience count more than keywords found only in Skills.
- Keywords found in Publications count as medium-strength evidence.

Categories:

- `Strong fit`: 70% or higher.
- `Moderate fit`: 40% to 69%.
- `Weak fit`: Below 40%.

This is a simple guide, not a final decision. A real application should still be reviewed by a person.

## Application Recommendation

Each report also recommends one next step:

- `Apply`: The keyword match is strong.
- `Apply after tailoring resume`: There is some overlap, but the resume should be customized first.
- `Low priority`: The current keyword match is weak and many important keywords are missing.

## Resume Tailoring Priorities

Each report groups missing keywords into:

- `Good to emphasize`
- `Transferable but needs careful wording`
- `Do not add unless true`

Do not add a keyword to your resume unless it is true for your actual experience.

This section uses simple rule tables in `job_helper.py`. It scans the job description for practical industry terms, checks whether the resume has related evidence, and adds a short explanation for each classification.

## Notes

- This project uses `pypdf` to read your resume PDF.
- The keyword extraction is simple and easy to understand.
- Always add only truthful skills and experience to your resume.
- If your resume PDF is scanned or image-only, the script may not be able to read it.
