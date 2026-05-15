"""
Industry-Oriented Job Application Helper

This beginner-friendly script reviews water treatment / UPW / environmental
engineering job descriptions against a PDF resume.

It is still rule-based and simple. It does not use AI or invent experience.
"""

from pathlib import Path
import csv
import json
import re


# ------------------------------------------------------------
# Project files
# ------------------------------------------------------------

DATA_DIR = Path("data")
JOBS_DIR = DATA_DIR / "jobs"
OUTPUTS_DIR = Path("outputs")

BASE_RESUME_FILE = DATA_DIR / "base_resume.pdf"
TARGET_KEYWORDS_FILE = DATA_DIR / "target_keywords.txt"
CRITICAL_KEYWORDS_FILE = DATA_DIR / "critical_keywords.txt"
SYNONYMS_FILE = DATA_DIR / "synonyms.json"
JOB_ROLE_PROFILES_FILE = DATA_DIR / "job_role_profiles.json"


# ------------------------------------------------------------
# Default keyword files
# ------------------------------------------------------------

DEFAULT_TARGET_KEYWORDS = [
    "water treatment",
    "wastewater",
    "UPW",
    "ultrapure water",
    "AOP",
    "advanced oxidation",
    "ozone",
    "UV",
    "reaction kinetics",
    "byproduct control",
    "contaminant removal",
    "process engineering",
    "process control",
    "process optimization",
    "water quality",
    "data interpretation",
    "data analysis",
    "technical reporting",
    "troubleshooting",
    "pilot testing",
    "laboratory analysis",
    "environmental engineering",
    "treatment performance",
]

DEFAULT_CRITICAL_KEYWORDS = [
    "UPW",
    "ultrapure water",
    "RO",
    "reverse osmosis",
    "semiconductor",
    "pilot testing",
    "process optimization",
    "water treatment",
    "ozone",
    "UV",
    "AOP",
    "advanced oxidation",
]

DEFAULT_SYNONYMS = {
    "process optimization": [
        "optimized reaction conditions",
        "optimized treatment conditions",
        "improved process performance",
        "treatment optimization",
        "optimized operating conditions",
    ],
    "data analysis": [
        "data interpretation",
        "interpreted water chemistry datasets",
        "analyzed water quality data",
        "interpreted treatment performance data",
        "evaluated technical datasets",
    ],
    "data interpretation": [
        "interpreted water chemistry datasets",
        "analyzed treatment performance",
        "evaluated water quality trends",
        "diagnosed water chemistry effects",
    ],
    "pilot testing": [
        "laboratory-scale evaluation",
        "bench-scale testing",
        "pilot-scale testing",
        "lab-scale evaluation",
        "experimental evaluation",
    ],
    "water treatment": [
        "treatment performance",
        "water quality evaluation",
        "contaminant removal",
        "treatment process",
    ],
    "UPW": [
        "ultrapure water",
        "high purity water",
        "trace contaminant control",
    ],
    "ultrapure water": [
        "UPW",
        "high purity water",
        "trace contaminant control",
    ],
    "AOP": [
        "advanced oxidation",
        "ozone UV",
        "UV ozone",
        "oxidation process",
    ],
    "advanced oxidation": [
        "AOP",
        "ozone UV",
        "UV ozone",
        "oxidation process",
    ],
    "byproduct control": [
        "DBP control",
        "byproduct formation",
        "disinfection byproduct control",
    ],
    "reaction kinetics": [
        "kinetic analysis",
        "reaction rate",
        "oxidant demand",
    ],
}


# Words that can make a resume sound more academic than industry-facing.
ACADEMIC_WORDS = {
    "investigated": "evaluated",
    "elucidated": "clarified",
    "mechanistic understanding": "process understanding",
    "studied": "assessed",
    "characterized": "evaluated",
    "examined": "assessed",
}


# Action verbs that are readable for ATS and industry hiring screens.
ACTION_VERBS = {
    "analyzed",
    "assessed",
    "built",
    "calculated",
    "coordinated",
    "designed",
    "developed",
    "evaluated",
    "implemented",
    "improved",
    "managed",
    "modeled",
    "monitored",
    "optimized",
    "prepared",
    "reported",
    "supported",
    "tested",
    "troubleshot",
    "validated",
}


# These lists keep tailoring suggestions realistic for the stated background.
SAFE_TO_EMPHASIZE = {
    "water treatment",
    "wastewater",
    "UPW",
    "ultrapure water",
    "AOP",
    "advanced oxidation",
    "ozone",
    "UV",
    "reaction kinetics",
    "byproduct control",
    "contaminant removal",
    "water quality",
    "data interpretation",
    "data analysis",
    "environmental engineering",
    "treatment performance",
}

TRANSFERABLE_KEYWORDS = {
    "pilot testing",
    "process optimization",
    "process engineering",
    "process control",
    "technical reporting",
    "troubleshooting",
    "laboratory analysis",
    "RO",
    "reverse osmosis",
}


# Job type patterns are simple keyword clues found in the job description.
# Add or remove phrases here if you want to tune the classifier later.
JOB_TYPE_PATTERNS = {
    "UPW engineer": [
        "UPW",
        "ultrapure water",
        "semiconductor",
        "fab",
        "cleanroom",
        "high purity water",
    ],
    "process engineer": [
        "process engineer",
        "process engineering",
        "process optimization",
        "process control",
        "operations",
        "plant",
        "equipment",
        "production",
    ],
    "R&D scientist": [
        "research",
        "scientist",
        "R&D",
        "laboratory",
        "bench-scale",
        "experimental",
        "reaction kinetics",
        "publication",
    ],
    "environmental engineer": [
        "environmental engineer",
        "environmental engineering",
        "wastewater",
        "stormwater",
        "compliance",
        "permitting",
        "regulatory",
    ],
    "consulting engineer": [
        "consulting",
        "client",
        "design",
        "proposal",
        "project delivery",
        "engineering services",
        "technical memorandum",
    ],
    "field engineer": [
        "field engineer",
        "field work",
        "site visit",
        "startup",
        "commissioning",
        "sampling",
        "inspection",
    ],
    "water treatment engineer": [
        "water treatment",
        "drinking water",
        "treatment plant",
        "filtration",
        "disinfection",
        "contaminant removal",
    ],
}


JOB_TYPE_PRIORITY_KEYWORDS = {
    "UPW engineer": ["UPW", "ultrapure water", "semiconductor", "RO", "reverse osmosis"],
    "process engineer": ["process optimization", "process control", "process engineering", "troubleshooting"],
    "R&D scientist": ["AOP", "advanced oxidation", "reaction kinetics", "laboratory analysis", "pilot testing"],
    "environmental engineer": ["environmental engineering", "wastewater", "water quality", "technical reporting"],
    "consulting engineer": ["technical reporting", "water treatment", "wastewater", "data analysis"],
    "field engineer": ["troubleshooting", "pilot testing", "water quality", "technical reporting"],
    "water treatment engineer": ["water treatment", "treatment performance", "water quality", "contaminant removal"],
}


# Role qualities can include wording that is broader than the target keyword list.
# These are used to slightly adjust scoring and make recommendations more specific.
JOB_TYPE_PRIORITY_TRAITS = {
    "UPW engineer": {
        "semiconductor / high-purity context": ["semiconductor", "fab", "cleanroom", "high purity", "UPW", "ultrapure water"],
        "membrane or polishing process relevance": ["RO", "reverse osmosis", "polishing", "filtration", "ion exchange"],
        "trace contaminant control": ["trace contaminant", "contaminant control", "TOC", "water quality"],
    },
    "process engineer": {
        "optimization and process improvement": ["optimize", "optimized", "optimization", "improved", "process improvement"],
        "operations and equipment language": ["operation", "operations", "plant", "equipment", "production", "startup"],
        "troubleshooting and process control": ["troubleshoot", "troubleshooting", "process control", "root cause", "corrective action"],
    },
    "consulting engineer": {
        "communication and reporting": ["report", "reporting", "technical memorandum", "presentation", "communicated", "documentation"],
        "project-oriented wording": ["project", "projects", "design", "proposal", "deliverable", "client"],
        "engineering decision support": ["recommendation", "evaluation", "assessment", "design support", "engineering decision"],
    },
    "R&D scientist": {
        "experimental and lab evidence": ["experiment", "experimental", "laboratory", "bench-scale", "lab-scale", "pilot"],
        "scientific depth": ["reaction kinetics", "mechanistic", "chemistry", "publication", "research"],
        "translation to application": ["developed", "evaluated", "performance", "scale", "application"],
    },
    "environmental engineer": {
        "compliance and reporting": ["compliance", "permit", "regulatory", "reporting", "standard"],
        "water quality and treatment": ["water quality", "wastewater", "treatment", "contaminant", "environmental"],
        "project support": ["project", "design", "assessment", "evaluation", "documentation"],
    },
    "field engineer": {
        "field and site readiness": ["field", "site", "inspection", "startup", "commissioning", "sampling"],
        "hands-on troubleshooting": ["troubleshooting", "equipment", "operation", "maintenance", "corrective"],
        "clear documentation": ["report", "documentation", "communicated", "checklist", "procedure"],
    },
    "water treatment engineer": {
        "treatment performance": ["treatment performance", "contaminant removal", "water quality", "process evaluation"],
        "applied process understanding": ["process", "operation", "optimization", "troubleshooting", "design"],
        "technical reporting": ["reporting", "documentation", "analysis", "assessment", "recommendation"],
    },
}


# ------------------------------------------------------------
# Basic file reading
# ------------------------------------------------------------


def read_text_file(file_path):
    """Read a text file and return its contents."""
    return file_path.read_text(encoding="utf-8")


def write_default_file(file_path, lines, description):
    """Create a default keyword file if it does not already exist."""
    if not file_path.exists():
        file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Created default {description}: {file_path}")


def load_keyword_file(file_path, default_lines, description):
    """
    Load a keyword file.

    The file should contain one keyword or phrase per line.
    Blank lines and lines starting with # are ignored.
    """
    write_default_file(file_path, default_lines, description)

    keywords = []
    for line in read_text_file(file_path).splitlines():
        keyword = line.strip()
        if keyword and not keyword.startswith("#"):
            keywords.append(keyword)

    return keywords


def create_default_synonyms_file():
    """Create data/synonyms.json if it does not exist."""
    if not SYNONYMS_FILE.exists():
        text = json.dumps(DEFAULT_SYNONYMS, indent=2)
        SYNONYMS_FILE.write_text(text + "\n", encoding="utf-8")
        print(f"Created default synonym file: {SYNONYMS_FILE}")


def load_synonyms():
    """
    Load semantic keyword relationships from data/synonyms.json.

    The JSON file maps one keyword to a list of related phrases.
    """
    create_default_synonyms_file()

    try:
        raw_synonyms = json.loads(read_text_file(SYNONYMS_FILE))
    except json.JSONDecodeError as error:
        print(f"Error: Could not read {SYNONYMS_FILE}.")
        print(f"Details: {error}")
        return {}

    synonyms = {}
    for keyword, related_phrases in raw_synonyms.items():
        if isinstance(related_phrases, list):
            synonyms[clean_keyword(keyword)] = [str(phrase) for phrase in related_phrases]

    return synonyms


ROLE_PROFILES_CACHE = None


def load_role_profiles():
    """Load transparent role-family rules from data/job_role_profiles.json."""
    global ROLE_PROFILES_CACHE

    if not JOB_ROLE_PROFILES_FILE.exists():
        print(f"Error: Role profile file not found: {JOB_ROLE_PROFILES_FILE}")
        print("Create this JSON file before running the analyzer.")
        ROLE_PROFILES_CACHE = {}
        return {}

    try:
        profiles = json.loads(read_text_file(JOB_ROLE_PROFILES_FILE))
    except json.JSONDecodeError as error:
        print(f"Error: Could not read {JOB_ROLE_PROFILES_FILE}.")
        print(f"Details: {error}")
        ROLE_PROFILES_CACHE = {}
        return {}

    cleaned_profiles = {}
    for role_name, profile in profiles.items():
        if isinstance(profile, dict):
            cleaned_profiles[str(role_name)] = profile

    ROLE_PROFILES_CACHE = cleaned_profiles
    return cleaned_profiles


def get_role_profiles():
    """Return cached role profiles, loading them if needed."""
    global ROLE_PROFILES_CACHE
    if ROLE_PROFILES_CACHE is None:
        return load_role_profiles()
    return ROLE_PROFILES_CACHE


def get_role_profile(role_name):
    """Return one role profile by display name."""
    return get_role_profiles().get(role_name, {})


def profile_list(profile, field_name):
    """Safely read a list field from a role profile."""
    value = profile.get(field_name, [])
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def role_academic_level(job_type):
    """Return low, moderate, or high academic tolerance for a role."""
    return str(get_role_profile(job_type).get("acceptable_academic_level", "moderate")).lower()


def role_name_has(job_type, phrase):
    """Case-insensitive helper for role-family checks."""
    return phrase.lower() in str(job_type).lower()


def read_resume_pdf(file_path):
    """
    Read text from a PDF resume using pypdf.

    If the resume is scanned or image-only, pypdf may not find text.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        print("Error: The pypdf package is not installed.")
        print("Install it in Windows PowerShell with:")
        print("python -m pip install -r requirements.txt")
        return None

    try:
        reader = PdfReader(file_path)
    except Exception as error:
        print(f"Error: Could not read the resume PDF: {file_path}")
        print(f"Details: {error}")
        return None

    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages_text.append(page_text)

    return "\n".join(pages_text).strip()


def read_resume_pdf_stream(file_obj):
    """
    Read text from an uploaded PDF-like object.

    This is used by the Streamlit app so users do not need to place files in
    the data folder.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("The pypdf package is not installed. Run: python -m pip install -r requirements.txt")

    try:
        file_obj.seek(0)
        reader = PdfReader(file_obj)
    except Exception as error:
        raise RuntimeError(f"Could not read the uploaded resume PDF. Details: {error}") from error

    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages_text.append(page_text)

    return "\n".join(pages_text).strip()


# ------------------------------------------------------------
# Text and keyword helpers
# ------------------------------------------------------------


def get_words(text):
    """Turn text into lowercase words."""
    return re.findall(r"[a-zA-Z][a-zA-Z+#.-]*", text.lower())


def simple_stem(word):
    """
    Do very light stemming.

    This is not a full NLP stemmer. It only helps beginner-friendly matching
    catch simple forms like optimize, optimized, and optimizing.
    """
    word = word.lower().strip(".:,;()[]")

    endings = ["ization", "ation", "ing", "ized", "ised", "ed", "es", "s"]
    for ending in endings:
        if len(word) > len(ending) + 3 and word.endswith(ending):
            return word[: -len(ending)]

    return word


def normalized_tokens(text):
    """Return lightly stemmed tokens for semantic overlap checks."""
    return {simple_stem(word) for word in get_words(text) if len(simple_stem(word)) >= 3}


def clean_keyword(keyword):
    """Normalize a keyword so comparisons are consistent."""
    return keyword.strip().lower()


def keyword_found_in_text(keyword, text):
    """Check whether a keyword or phrase appears in text."""
    keyword_pattern = re.escape(clean_keyword(keyword))
    keyword_pattern = keyword_pattern.replace(r"\ ", r"\s+")
    pattern = rf"(?<![a-z0-9]){keyword_pattern}(?![a-z0-9])"

    return re.search(pattern, text.lower()) is not None


def semantic_keyword_match(keyword, text, synonyms):
    """
    Check for exact or semantic keyword matches.

    Match types:
    - exact: the keyword phrase appears directly.
    - synonym: a related phrase from data/synonyms.json appears.
    - token overlap: most words from a related phrase appear in the text.
    """
    if keyword_found_in_text(keyword, text):
        return {
            "matched": True,
            "match_type": "exact",
            "evidence": keyword,
            "strength": 1.0,
        }

    keyword_key = clean_keyword(keyword)
    related_phrases = synonyms.get(keyword_key, [])
    text_tokens = normalized_tokens(text)

    for phrase in related_phrases:
        if keyword_found_in_text(phrase, text):
            return {
                "matched": True,
                "match_type": "synonym",
                "evidence": phrase,
                "strength": 0.75,
            }

        phrase_tokens = normalized_tokens(phrase)
        if len(phrase_tokens) >= 2:
            overlap = phrase_tokens & text_tokens
            overlap_rate = len(overlap) / len(phrase_tokens)
            if overlap_rate >= 0.60:
                return {
                    "matched": True,
                    "match_type": "token overlap",
                    "evidence": phrase,
                    "strength": 0.60,
                }

    return {
        "matched": False,
        "match_type": "none",
        "evidence": "",
        "strength": 0.0,
    }


def find_keyword_matches(keywords, text, synonyms):
    """Return detailed keyword matches for the given text."""
    matches = {}
    for keyword in keywords:
        match = semantic_keyword_match(keyword, text, synonyms)
        if match["matched"]:
            matches[keyword] = match
    return matches


def find_keywords_in_text(keywords, text, synonyms=None):
    """Return keywords that appear in text exactly or semantically."""
    if synonyms is None:
        synonyms = {}

    found = []
    for keyword in keywords:
        if semantic_keyword_match(keyword, text, synonyms)["matched"]:
            found.append(keyword)
    return found


def score_role_profile_match(job_text, profile):
    """Score one role profile against a JD using plain phrase matching."""
    score = 0.0
    for pattern in profile_list(profile, "detection_patterns"):
        if keyword_found_in_text(pattern, job_text):
            score += 2.0
    for skill in profile_list(profile, "priority_skills"):
        if keyword_found_in_text(skill, job_text):
            score += 1.0
    return score


def detect_job_type(job_text, role_profiles=None):
    """
    Guess the role family from JSON profile patterns.

    This is a simple scoring system. The category with the most matching
    phrases wins. If nothing matches, the category is "general engineering".
    """
    if role_profiles is None:
        role_profiles = get_role_profiles()

    scores = {}

    for job_type, profile in role_profiles.items():
        score = score_role_profile_match(job_text, profile)
        scores[job_type] = score

    best_job_type = "general engineering"
    best_score = 0.0
    for job_type, score in scores.items():
        if score > best_score:
            best_job_type = job_type
            best_score = score

    return best_job_type, scores


def get_job_type_priority_keywords(job_type):
    """Return keywords that matter more for a specific job type."""
    profile = get_role_profile(job_type)
    if profile:
        return profile_list(profile, "priority_skills")
    return JOB_TYPE_PRIORITY_KEYWORDS.get(job_type, [])


def get_job_type_priority_traits(job_type):
    """Return broader role qualities that matter for a specific job type."""
    profile = get_role_profile(job_type)
    if isinstance(profile.get("role_traits"), dict):
        return profile["role_traits"]
    return JOB_TYPE_PRIORITY_TRAITS.get(job_type, {})


def create_job_type_notes(job_type):
    """Explain how the review priorities shift for this job type."""
    profile = get_role_profile(job_type)
    if profile:
        notes = []
        priority_skills = profile_list(profile, "priority_skills")[:6]
        transferable = profile_list(profile, "transferable_engineering_skills")[:5]

        if priority_skills:
            notes.append("Priority skills for this role family: " + ", ".join(priority_skills) + ".")
        if profile.get("preferred_language_style"):
            notes.append("Preferred language style: " + str(profile["preferred_language_style"]))
        notes.append("Acceptable academic depth: " + role_academic_level(job_type) + ".")
        notes.append(
            "Operational/process emphasis: "
            + str(profile.get("operational_process_emphasis", "medium"))
            + "; reporting/consulting emphasis: "
            + str(profile.get("reporting_consulting_emphasis", "medium"))
            + "."
        )
        if transferable:
            notes.append("Transferable engineering skills to position carefully: " + ", ".join(transferable) + ".")
        return notes

    if job_type == "R&D scientist":
        return [
            "Academic or research wording is more acceptable for this role, especially when tied to technical outcomes.",
            "Prioritize experimental design, reaction kinetics, AOP chemistry, publications, and lab or pilot evidence.",
        ]
    if job_type == "process engineer":
        return [
            "Prioritize operational language, troubleshooting, process control, equipment, and optimization outcomes.",
            "Academic wording should be translated toward plant, process, quality, or production impact when accurate.",
        ]
    if job_type == "UPW engineer":
        return [
            "Prioritize semiconductor, UPW, ultrapure water, RO, trace contaminant control, and high-purity water relevance.",
            "Make sure UPW evidence appears early and is supported by technical bullets, not only a skills list.",
        ]
    if job_type == "environmental engineer":
        return [
            "Prioritize wastewater, environmental compliance, water quality, reporting, and treatment performance.",
            "Connect technical analysis to practical environmental engineering decisions.",
        ]
    if role_name_has(job_type, "wastewater"):
        if has_data or has_water_quality:
            sentences.append(
                "Brings water quality data interpretation and treatment performance evaluation experience that can support wastewater process analysis."
            )
        sentences.append(
            "Tailoring should address the JD's specific design, modeling, hydraulics, and deliverable requirements only where supported."
        )
    elif role_name_has(job_type, "consult"):
        return [
            "Prioritize client-facing technical reporting, design support, project work, and clear communication.",
            "Make analysis sound useful for engineering decisions, not only research findings.",
        ]
    if job_type == "field engineer":
        return [
            "Prioritize site work, troubleshooting, sampling, commissioning, and hands-on technical support.",
            "Show practical field readiness where your experience honestly supports it.",
        ]
    if job_type == "water treatment engineer":
        return [
            "Prioritize treatment performance, process evaluation, contaminant removal, and water quality outcomes.",
            "Use industry treatment language while keeping technical claims accurate.",
        ]
    return [
        "No specific job type dominated, so the review uses general water treatment and environmental engineering priorities.",
    ]


def text_has_trait(text, trait_patterns, synonyms):
    """Check whether any phrase for a role trait appears in text."""
    for pattern in trait_patterns:
        if semantic_keyword_match(pattern, text, synonyms)["matched"]:
            return True
    return False


def analyze_role_specific_priorities(job_type, job_text, resume_text, synonyms):
    """
    Compare role-specific qualities requested by the job with the resume.

    This is intentionally simple: if the job seems to request a trait, the
    resume gets credit when it shows related wording.
    """
    traits = get_job_type_priority_traits(job_type)
    matched = []
    missing = []

    for trait_name, patterns in traits.items():
        job_requests_trait = text_has_trait(job_text, patterns, synonyms)
        resume_supports_trait = text_has_trait(resume_text, patterns, synonyms)

        if job_requests_trait and resume_supports_trait:
            matched.append(f"{trait_name}: supported by resume wording.")
        elif job_requests_trait:
            missing.append(f"{trait_name}: important for this {job_type} role but not clearly visible in the resume.")

    if not traits:
        return {
            "matched": [],
            "missing": [],
            "match_rate": 0,
        }

    requested_count = len(matched) + len(missing)
    if requested_count == 0:
        match_rate = 0
    else:
        match_rate = round((len(matched) / requested_count) * 100)

    return {
        "matched": matched,
        "missing": missing,
        "match_rate": match_rate,
    }


def remove_keywords(keywords, keywords_to_remove):
    """Remove critical keywords from the normal keyword list."""
    remove_set = {clean_keyword(keyword) for keyword in keywords_to_remove}
    return [keyword for keyword in keywords if clean_keyword(keyword) not in remove_set]


def find_missing_keywords(job_keywords, resume_keywords):
    """Return job keywords that do not appear in the resume."""
    resume_set = {clean_keyword(keyword) for keyword in resume_keywords}
    return [keyword for keyword in job_keywords if clean_keyword(keyword) not in resume_set]


def find_matched_keywords(job_keywords, resume_keywords):
    """Return job keywords that also appear in the resume."""
    resume_set = {clean_keyword(keyword) for keyword in resume_keywords}
    return [keyword for keyword in job_keywords if clean_keyword(keyword) in resume_set]


# ------------------------------------------------------------
# Resume sections and bullets
# ------------------------------------------------------------


def detect_resume_sections(resume_text):
    """
    Split the resume into rough sections.

    This is intentionally simple. It looks for common section headings and
    groups following lines under that section.
    """
    section_names = {
        "summary": {"summary", "profile", "objective"},
        "skills": {"skills", "technical skills", "core skills"},
        "experience": {"experience", "work experience", "professional experience", "projects"},
        "education": {"education"},
        "publications": {"publications", "publication", "research", "conference"},
    }

    sections = {
        "summary": "",
        "skills": "",
        "experience": "",
        "education": "",
        "publications": "",
        "other": "",
    }
    raw_lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    normalized_lines = [line.lower().strip(":") for line in raw_lines]
    heading_lines_to_ignore = set()
    all_headings = set().union(*section_names.values())

    for index in range(min(12, len(normalized_lines) - 1)):
        if normalized_lines[index] in all_headings and normalized_lines[index + 1] in all_headings:
            heading_lines_to_ignore.add(index)
            heading_lines_to_ignore.add(index + 1)

    current_section = "other"
    skill_category_headings = {
        "process evaluation & water treatment",
        "analytical & laboratory",
        "instrumentation",
        "technical analysis & software",
    }
    experience_title_pattern = re.compile(
        r"\b(researcher|research assistant|engineer|scientist|intern|specialist|manager|consultant)\b.*\b(19|20)\d{2}\b",
        re.IGNORECASE,
    )
    degree_pattern = re.compile(
        r"^(ph\.?d\.?|m\.?s\.?|b\.?s\.?|master|bachelor|doctor)",
        re.IGNORECASE,
    )

    for line_index, clean_line in enumerate(raw_lines):
        lower_line = clean_line.lower().strip(":")
        found_heading = None

        if line_index not in heading_lines_to_ignore:
            for section, headings in section_names.items():
                if lower_line in headings:
                    found_heading = section
                    break

        if found_heading:
            current_section = found_heading
        elif lower_line in skill_category_headings:
            current_section = "skills"
            sections[current_section] += clean_line + "\n"
        elif experience_title_pattern.search(clean_line) and not degree_pattern.search(clean_line):
            current_section = "experience"
            sections[current_section] += clean_line + "\n"
        elif degree_pattern.search(clean_line):
            current_section = "education"
            sections[current_section] += clean_line + "\n"
        elif current_section == "education" and get_bullet_action_verb(clean_line) in ACTION_VERBS:
            sections["experience"] += clean_line + "\n"
        else:
            sections[current_section] += clean_line + "\n"

    return sections


def find_keyword_sections(keywords, sections, synonyms):
    """Find which resume sections contain each keyword."""
    keyword_sections = {}

    for keyword in keywords:
        found_sections = []
        for section_name, section_text in sections.items():
            if semantic_keyword_match(keyword, section_text, synonyms)["matched"]:
                found_sections.append(section_name)
        keyword_sections[keyword] = found_sections

    return keyword_sections


def section_importance(keyword, keyword_sections):
    """
    Give more credit to keywords found in Experience.

    Skills-only matches are useful, but they are weaker than proof inside
    experience bullets. Publications are medium strength.
    """
    sections = keyword_sections.get(keyword, [])

    if "experience" in sections:
        return 1.20
    if "publications" in sections:
        return 0.90
    if "summary" in sections:
        return 0.85
    if "skills" in sections:
        return 0.70
    if "education" in sections:
        return 0.75
    return 0.60


def detect_resume_bullets(resume_text):
    """
    Detect likely resume bullets.

    PDF text extraction can lose bullet symbols, so this also keeps concise
    action-oriented lines that look like resume bullet content.
    """
    bullets = []

    for line in resume_text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue

        starts_like_bullet = clean_line.startswith(("-", "*", "•", "–"))
        word_count = len(get_words(clean_line))
        starts_with_action = get_bullet_action_verb(clean_line) in ACTION_VERBS

        if starts_like_bullet:
            bullets.append(clean_line.lstrip("-*•– ").strip())
        elif 6 <= word_count <= 45 and starts_with_action:
            bullets.append(clean_line)

    # Fallback: if no bullets were detected, use sentence-like lines.
    if not bullets:
        for sentence in re.split(r"(?<=[.!?])\s+", resume_text):
            sentence = sentence.strip()
            if 8 <= len(get_words(sentence)) <= 45:
                bullets.append(sentence)

    return bullets


def find_bullet_section(bullet, sections):
    """Guess which resume section contains a bullet."""
    for section_name, section_text in sections.items():
        if bullet in section_text:
            return section_name
    return "other"


def get_bullet_action_verb(bullet):
    """
    Return the likely action verb for a bullet.

    This handles both:
    - "Evaluated treatment performance..."
    - "UPW Contaminant Control: Optimized UV..."
    """
    if ":" in bullet:
        after_colon = bullet.split(":", 1)[1].strip()
        if after_colon:
            return after_colon.split()[0].lower().strip(".,:;")

    if bullet.split():
        return bullet.split()[0].lower().strip(".,:;")

    return ""


def score_bullet_relevance(bullet, job_keywords, critical_keywords, synonyms):
    """Score one bullet against the job keywords."""
    score = 0
    matched = []
    critical_set = {clean_keyword(keyword) for keyword in critical_keywords}

    for keyword in job_keywords:
        match = semantic_keyword_match(keyword, bullet, synonyms)
        if match["matched"]:
            matched.append(keyword)
            if clean_keyword(keyword) in critical_set:
                score += 3 * match["strength"]
            else:
                score += match["strength"]

    return score, matched


TRANSFERABLE_BULLET_SKILL_RULES = {
    "process optimization": ["optimized", "optimization", "improve", "improved", "operational decision"],
    "process conditions": ["conditions", "pH", "oxidant", "matrix", "UV", "ozone", "halogen"],
    "treatment performance": ["treatment performance", "contaminant removal", "water quality", "control"],
    "engineering evaluation": ["assessed", "evaluated", "interpreted", "diagnosed", "selection", "tradeoffs"],
    "troubleshooting": ["diagnosed", "troubleshot", "exceedance", "limits", "drivers"],
    "root-cause analysis": ["diagnosed", "pH", "matrix-dependent", "drivers", "cause", "effects"],
    "data interpretation": ["interpreted", "data", "datasets", "analysis", "water chemistry"],
    "process evaluation": ["bench-scale", "process evaluation", "treatment selection", "performance assessment"],
    "data analysis": ["interpreted", "data", "analysis", "kinetics", "water quality data"],
    "technical reporting": ["reported", "communicated", "reports", "presentations", "manuscripts"],
    "treatment performance evaluation": ["kinetics", "contaminant removal", "DBP", "water quality", "performance"],
    "engineering decision support": ["recommendation", "decision-making", "tradeoffs", "selection", "implications"],
}


TRANSFERABLE_SKILL_JOB_TRIGGERS = {
    "process optimization": ["process optimization", "improvement", "improvements", "adjust the process", "process changes"],
    "process conditions": ["process conditions", "operating conditions", "quality requirements", "adjust the process"],
    "treatment performance": ["treatment performance", "performance", "quality", "treatment"],
    "engineering evaluation": ["analysis", "alternative analysis", "engineering principles", "critical thinking"],
    "troubleshooting": ["troubleshoot", "solve process problems", "process problems", "equipment issues"],
    "root-cause analysis": ["root cause", "solve process problems", "troubleshoot", "non-conformances"],
    "data interpretation": ["data analysis", "statistical data analysis", "analysis", "monitor"],
    "process evaluation": ["process", "engineering support", "design options", "operation unit"],
    "data analysis": ["data analysis", "statistical", "compile", "monitor", "reports"],
    "technical reporting": ["reports", "technical memoranda", "business writing", "documentation"],
    "treatment performance evaluation": ["wastewater treatment", "treatment process", "quality requirements", "performance"],
    "engineering decision support": ["design options", "recommendations", "client presentations", "engineering planning"],
}


def transferable_skill_requested(skill, job_text, job_type):
    """Check whether a transferable skill is relevant to this JD or role profile."""
    if any_phrase_found(TRANSFERABLE_SKILL_JOB_TRIGGERS.get(skill, []), job_text):
        return True

    profile = get_role_profile(job_type)
    profile_terms = profile_list(profile, "priority_skills") + profile_list(profile, "transferable_engineering_skills")
    return any(clean_keyword(skill) in clean_keyword(term) or clean_keyword(term) in clean_keyword(skill) for term in profile_terms)


def match_transferable_bullet_skills(bullet, job_text, job_type):
    """Find transparent transferable skill matches for a resume bullet."""
    matches = []

    for skill, bullet_phrases in TRANSFERABLE_BULLET_SKILL_RULES.items():
        if not any_phrase_found(bullet_phrases, bullet):
            continue
        if transferable_skill_requested(skill, job_text, job_type):
            matches.append(skill)

    return matches


def classify_bullet_match(direct_keywords, transferable_skills):
    """Label one bullet as direct, transferable, or low relevance."""
    if direct_keywords:
        return "Direct match"
    if transferable_skills:
        return "Transferable match"
    return "Low relevance"


def create_bullet_reason(match_type, direct_keywords, transferable_skills):
    """Create a short, practical reason for one bullet classification."""
    if match_type == "Direct match" and transferable_skills:
        return "Direct JD terms plus transferable skills."
    if match_type == "Direct match":
        return "Direct JD keyword match."
    if match_type == "Transferable match":
        return "Relevant transferable engineering work."
    return "Limited JD or role-profile overlap."


def analyze_resume_bullets(resume_text, sections, job_keywords, critical_keywords, synonyms, job_text="", job_type=""):
    """Classify bullets by direct and transferable relevance."""
    bullets = detect_resume_bullets(resume_text)
    scored_bullets = []

    for bullet in bullets:
        score, matched = score_bullet_relevance(bullet, job_keywords, critical_keywords, synonyms)
        transferable = match_transferable_bullet_skills(bullet, job_text, job_type)
        match_type = classify_bullet_match(matched, transferable)
        combined_score = score + (0.75 * len(transferable))
        section = find_bullet_section(bullet, sections)
        scored_bullets.append(
            {
                "text": bullet,
                "score": combined_score,
                "matched": matched,
                "transferable": transferable,
                "match_type": match_type,
                "reason": create_bullet_reason(match_type, matched, transferable),
                "section": section,
                "word_count": len(get_words(bullet)),
            }
        )

    strongest = [item for item in scored_bullets if item["match_type"] == "Direct match"]
    strongest = sorted(strongest, key=lambda item: item["score"], reverse=True)[:3]

    transferable = [item for item in scored_bullets if item["match_type"] == "Transferable match"]
    transferable = sorted(transferable, key=lambda item: item["score"], reverse=True)[:5]

    low = [item for item in scored_bullets if item["match_type"] == "Low relevance"]
    low = low[:2]

    return strongest, transferable, low


# ------------------------------------------------------------
# Scoring and recommendations
# ------------------------------------------------------------


def calculate_weighted_fit_score(
    job_critical,
    job_normal,
    matched_critical,
    matched_normal,
    keyword_sections,
    resume_match_details,
):
    """
    Calculate a weighted fit score.

    Critical keywords count 3 points. Normal keywords count 1 point.
    Resume section placement adjusts the matched score slightly.
    """
    possible_score = len(job_critical) * 3 + len(job_normal)
    if possible_score == 0:
        return 0

    earned_score = 0
    for keyword in matched_critical:
        match_strength = resume_match_details.get(keyword, {}).get("strength", 1.0)
        earned_score += 3 * match_strength * section_importance(keyword, keyword_sections)
    for keyword in matched_normal:
        match_strength = resume_match_details.get(keyword, {}).get("strength", 1.0)
        earned_score += match_strength * section_importance(keyword, keyword_sections)

    return min(100, round((earned_score / possible_score) * 100))


def calculate_role_profile_fit_score(job_type, job_text, resume_text, synonyms):
    """Score fit against the detected role profile's own transparent rules."""
    profile = get_role_profile(job_type)
    if not profile:
        return 0

    requested = []
    supported = []

    for skill in profile_list(profile, "priority_skills"):
        if semantic_keyword_match(skill, job_text, synonyms)["matched"]:
            requested.append(skill)
            if semantic_keyword_match(skill, resume_text, synonyms)["matched"]:
                supported.append(skill)

    for trait_name, patterns in get_job_type_priority_traits(job_type).items():
        if text_has_trait(job_text, patterns, synonyms):
            requested.append(trait_name)
            if text_has_trait(resume_text, patterns, synonyms):
                supported.append(trait_name)

    if not requested:
        return 0

    return round((len(supported) / len(requested)) * 100)


DOMAIN_ALIGNMENT_AREAS = {
    "water treatment": ["water treatment", "treatment plant", "drinking water", "filtration", "disinfection"],
    "wastewater": ["wastewater", "wastewater treatment", "industrial wastewater", "biological treatment"],
    "environmental engineering": ["environmental engineering", "environmental engineer", "environmental treatment", "environmental water"],
    "UPW": ["UPW", "ultrapure water", "high purity water", "semiconductor water"],
    "industrial water": ["industrial water", "process water", "water reuse", "reclamation"],
    "treatment chemistry": ["treatment chemistry", "reaction kinetics", "oxidant", "DBP", "water chemistry"],
    "contaminant control": ["contaminant control", "contaminant removal", "trace contaminant", "PFAS", "TOC"],
    "advanced oxidation": ["advanced oxidation", "AOP", "ozone", "UV"],
    "water quality": ["water quality", "water quality data", "analytical", "sample analysis"],
}


def domain_area_found(area_phrases, text, synonyms):
    """Return True when any phrase for a water-domain area appears in text."""
    for phrase in area_phrases:
        if phrase_found_loose(phrase, text):
            return True
    return False


def calculate_domain_alignment_score(job_text, resume_text, synonyms):
    """
    Score water-domain overlap separately from general engineering transfer.

    If the JD is not water/environmental/industrial-water related, the score is
    intentionally capped at a modest baseline so transferable skills do not
    overpower domain mismatch.
    """
    requested_areas = []
    supported_areas = []

    for area_name, phrases in DOMAIN_ALIGNMENT_AREAS.items():
        if domain_area_found(phrases, job_text, synonyms):
            requested_areas.append(area_name)
            if domain_area_found(phrases, resume_text, synonyms):
                supported_areas.append(area_name)

    if not requested_areas:
        return {
            "score": 35,
            "requested": [],
            "supported": [],
            "note": "Water-domain relevance is not central in this JD; transferable engineering evidence is secondary.",
        }

    score = round((len(supported_areas) / len(requested_areas)) * 100)
    return {
        "score": score,
        "requested": requested_areas,
        "supported": supported_areas,
        "note": "Domain score reflects overlap in water, wastewater, environmental, UPW, industrial water, treatment chemistry, contaminant control, advanced oxidation, and water quality areas.",
    }


def combine_fit_scores(keyword_score, role_profile_score, domain_score, job_keyword_count):
    """
    Combine fit components with domain relevance as the largest factor.

    Domain relevance is very important, direct role overlap is important, and
    transferable role evidence is supportive but secondary.
    """
    if job_keyword_count == 0:
        return round((domain_score * 0.45) + (role_profile_score * 0.45) + (keyword_score * 0.10))

    return round((domain_score * 0.50) + (role_profile_score * 0.30) + (keyword_score * 0.20))


def emphasis_bonus_value(emphasis):
    """Convert low/medium/high emphasis strings into small score modifiers."""
    emphasis = str(emphasis).lower()
    if emphasis == "high":
        return 2
    if emphasis == "low":
        return 0
    return 1


def adjust_score_for_job_type(score, job_type, all_job_keywords, matched_keywords, job_text="", resume_text="", synonyms=None):
    """
    Add a modest role-profile adjustment.

    Priority skills come from data/job_role_profiles.json when available. The
    adjustment stays small so the report remains easy to reason about.
    """
    if synonyms is None:
        synonyms = {}

    priority_keywords = get_job_type_priority_keywords(job_type)
    if not priority_keywords:
        return score

    if job_text and resume_text:
        requested_priority = [
            keyword
            for keyword in priority_keywords
            if semantic_keyword_match(keyword, job_text, synonyms)["matched"]
        ]
        matched_priority = [
            keyword
            for keyword in requested_priority
            if semantic_keyword_match(keyword, resume_text, synonyms)["matched"]
        ]
    else:
        job_priority = set(clean_keyword(keyword) for keyword in all_job_keywords) & set(
            clean_keyword(keyword) for keyword in priority_keywords
        )
        matched_priority = set(clean_keyword(keyword) for keyword in matched_keywords) & job_priority
        requested_priority = list(job_priority)

    if not requested_priority:
        return score

    priority_match_rate = len(matched_priority) / len(requested_priority)
    profile = get_role_profile(job_type)
    emphasis_bonus = emphasis_bonus_value(profile.get("operational_process_emphasis", "medium"))
    emphasis_bonus += emphasis_bonus_value(profile.get("reporting_consulting_emphasis", "medium"))
    bonus = round(priority_match_rate * (4 + emphasis_bonus))

    return min(100, score + bonus)


def adjust_score_for_role_priorities(score, role_priority_alignment):
    """
    Slightly adjust score based on broader role-specific qualities.

    The adjustment is modest so keyword evidence still drives the main score.
    """
    matched_count = len(role_priority_alignment["matched"])
    missing_count = len(role_priority_alignment["missing"])

    if matched_count == 0 and missing_count == 0:
        return score

    bonus = min(8, matched_count * 3)
    penalty = min(8, missing_count * 3)

    return max(0, min(100, score + bonus - penalty))


def adjust_score_for_role_specific_gaps(score, role_specific_gaps):
    """Reduce overconfident keyword scores when concrete JD requirements are missing."""
    if not role_specific_gaps:
        return score

    penalty = min(18, len(role_specific_gaps) * 4)
    return max(0, min(100, round(score - penalty)))


def choose_fit_category(score):
    """Choose a simple fit category from the score."""
    if score >= 70:
        return "Strong fit"
    if score >= 55:
        return "Moderate fit"
    if score >= 40:
        return "Moderate-low fit"
    return "Weak fit"


def choose_domain_alignment_label(score):
    """Use simple language for domain alignment in the report."""
    if score >= 70:
        return "Strong"
    if score >= 45:
        return "Moderate"
    return "Low"


def create_application_recommendation(
    score,
    missing_critical,
    missing_normal,
    job_keyword_count,
    role_priority_alignment,
    role_specific_gaps,
    job_type,
):
    """Recommend whether this job should be a priority."""
    role_gaps = role_priority_alignment["missing"]

    if job_keyword_count == 0:
        if score >= 40 and role_specific_gaps:
            gap_names = [gap.split(":", 1)[0] for gap in role_specific_gaps[:3]]
            return (
                "Apply after tailoring resume",
                "The posting does not match the water/UPW keyword list, but the detected role family has transferable overlap. Address specific gaps such as "
                + ", ".join(gap_names)
                + " only where true.",
            )
        if score >= 40:
            return (
                "Consider applying",
                f"The posting does not match the water/UPW keyword list, but the resume shows some {job_type} role-family overlap. Tailor toward the role profile before applying.",
            )
        if role_priority_alignment["matched"]:
            return (
                "Low priority",
                f"The posting has some {job_type} signals, but it does not include keywords from the water treatment / UPW target lists. Treat it as lower priority unless you want a broader process role outside your strongest water-focused positioning.",
            )
        return (
            "Low priority",
            "The job description did not include keywords from the target or critical keyword lists. Review it manually, but the current keyword evidence does not show a strong water treatment or UPW fit.",
        )

    if not missing_critical and not role_gaps and not role_specific_gaps and score >= 70:
        return (
            "Apply",
            f"The resume matches the main industry keywords and supports the main {job_type} priorities. Tailor the wording lightly, but this is a strong target.",
        )

    if score >= 40 or len(missing_critical) <= 2:
        if role_specific_gaps:
            gap_names = [gap.split(":", 1)[0] for gap in role_specific_gaps[:3]]
            reason = (
                "There is useful overlap, but the JD asks for specific requirements not clearly shown in the resume: "
                + ", ".join(gap_names)
                + ". Tailor only where your real experience supports the wording."
            )
        elif role_gaps:
            reason = (
                f"There is useful overlap, but the resume should better show {job_type} priorities such as "
                + "; ".join(role_gaps[:2])
                + " Tailor only where your real experience supports the wording."
            )
        else:
            reason = (
                "There is useful overlap, but important keywords are missing or not strongly supported in the resume. "
                "Tailor the resume only where your real water treatment, UPW, AOP, or data work supports the wording."
            )
        return (
            "Apply after tailoring resume",
            reason,
        )

    return (
        "Low priority",
        "The resume currently misses several high-priority industry keywords for this job. Review manually, but prioritize stronger matches unless you can truthfully support the missing areas.",
    )


GOOD_TO_EMPHASIZE_RULES = {
    "process optimization": ["optimized", "optimization", "treatment performance", "reaction kinetics"],
    "data analysis": ["data interpretation", "analysis", "water quality data", "datasets"],
    "treatment performance": ["treatment performance", "contaminant removal", "water quality"],
    "technical reporting": ["report", "reporting", "technical", "documentation"],
    "water quality interpretation": ["water quality", "data interpretation", "analysis"],
    "byproduct control": ["byproduct", "DBP", "bromide", "bromate", "bromine"],
    "contaminant control": ["contaminant", "trace contaminant", "contaminant removal"],
}


GOOD_TO_EMPHASIZE_JOB_TRIGGERS = {
    "process optimization": ["process changes", "process conditions", "improvement", "improvements", "adjust the process"],
    "data analysis": ["monitor", "reports", "compile", "analysis", "quality"],
    "treatment performance": ["quality requirements", "process conditions", "performance", "monitor"],
    "technical reporting": ["reports", "business writing", "documentation", "procedures", "checklists"],
    "water quality interpretation": ["quality", "monitor products quality", "requirements"],
    "byproduct control": ["byproduct", "emissions", "releases", "non-conformances"],
    "contaminant control": ["containment", "cleanup", "emissions", "releases"],
}


TRANSFERABLE_TAILORING_RULES = {
    "pilot testing": ["laboratory", "bench-scale", "lab-scale", "experimental", "evaluation"],
    "scale-up": ["pilot", "bench-scale", "lab-scale", "treatment performance"],
    "troubleshooting": ["diagnosed", "troubleshot", "analysis", "root cause"],
    "manufacturing support": ["industrial", "process", "quality", "support"],
    "process support": ["process", "treatment performance", "technical support"],
    "design support": ["assessed", "evaluated", "recommendation", "process evaluation", "treatment selection"],
    "client communication": ["collaboration", "working group", "communication", "reported"],
    "project coordination": ["project", "working group", "collaboration", "coordinated"],
}


TRANSFERABLE_JOB_TRIGGERS = {
    "pilot testing": ["startup", "start-up", "testing", "trial"],
    "scale-up": ["start-up", "startup", "expansion", "production"],
    "troubleshooting": ["troubleshoot", "solve process problems", "process problems"],
    "manufacturing support": ["production", "plant", "shift", "maintenance", "operations"],
    "process support": ["engineering support", "process conditions", "operation unit", "day personnel"],
    "design support": ["design", "design options", "plans and specifications", "engineering planning", "cost estimates"],
    "client communication": ["communication skills", "vendors", "interpersonal", "customer service", "client", "presentations"],
    "project coordination": ["project management", "projects", "management of change", "MOC"],
}


WATER_CONSULTING_PRIORITY_ORDER = [
    "technical reporting",
    "treatment performance",
    "wastewater",
    "water quality interpretation",
    "design support",
    "project coordination",
    "client communication",
]


PROCESS_MANUFACTURING_PRIORITY_ORDER = [
    "manufacturing support",
    "process support",
    "troubleshooting",
    "process optimization",
    "plant operations",
]


MANUFACTURING_SUPPORT_JOB_SIGNALS = [
    "manufacturing",
    "plant production",
    "production",
    "plant operations",
    "operations",
    "operating unit",
]


DO_NOT_ADD_RULES = {
    "AutoCAD": ["autocad"],
    "PLC": ["plc"],
    "SCADA": ["scada"],
    "P&ID": ["p&id", "piping and instrumentation"],
    "construction management": ["construction management"],
    "wastewater plant operation": ["wastewater plant operation", "plant operation", "operator"],
    "field sampling": ["field sampling", "sampling"],
    "regulatory permitting": ["permitting", "permit", "regulatory permit"],
    "HAZOP": ["hazop"],
}


def phrase_found_loose(phrase, text):
    """Check whether a phrase appears with a simple case-insensitive search."""
    return phrase.lower() in text.lower()


def any_phrase_found(phrases, text):
    """Return True if any phrase in a list appears in the text."""
    for phrase in phrases:
        if phrase_found_loose(phrase, text):
            return True
    return False


WATER_TREATMENT_JOB_SIGNALS = [
    "water treatment",
    "wastewater",
    "drinking water",
    "ultrapure water",
    "upw",
    "semiconductor water",
    "environmental engineering",
    "treatment process",
    "treatment plant",
    "contaminant",
    "disinfection",
    "advanced oxidation",
    "ozone",
    "uv",
]


def is_water_treatment_related_job(job_text):
    """Return True when UPW/AOP/water-treatment differentiators fit the JD."""
    return any_phrase_found(WATER_TREATMENT_JOB_SIGNALS, job_text)


ROLE_SPECIFIC_REQUIREMENT_RULES = [
    {
        "name": "BioWin/GPSX/Sumo wastewater modeling",
        "job_phrases": ["biowin", "gpsx", "sumo", "commercial software", "biological modelling", "biological modeling"],
        "resume_phrases": ["biowin", "gpsx", "sumo", "biological model", "wastewater model", "process model"],
        "note": "Specific wastewater process-modeling software is requested, but the resume mainly shows treatment data interpretation and kinetic modeling.",
    },
    {
        "name": "P&ID review or updates",
        "job_phrases": ["p&id", "piping and instrumentation"],
        "resume_phrases": ["p&id", "piping and instrumentation"],
        "note": "P&ID ownership is requested and is not clearly shown.",
    },
    {
        "name": "Management of Change (MOC)",
        "job_phrases": ["management of change", "moc", "mocs"],
        "resume_phrases": ["management of change", "moc", "change control"],
        "note": "MOC/change-control responsibility is requested and is not clearly shown.",
    },
    {
        "name": "Cost estimates",
        "job_phrases": ["cost estimate", "cost estimates", "budget", "cost reports"],
        "resume_phrases": ["cost estimate", "cost estimates", "budget owner", "budgeting"],
        "note": "Cost-estimate or budget ownership is not clearly supported beyond adjacent cost-related considerations.",
    },
    {
        "name": "Plans and specifications",
        "job_phrases": ["plans and specifications", "plans/specifications", "specifications"],
        "resume_phrases": ["plans and specifications", "plans/specifications", "specifications", "design package"],
        "note": "Engineering plans/specifications preparation is requested and is not clearly shown.",
    },
    {
        "name": "Hydraulics",
        "job_phrases": ["hydraulics", "hydraulic"],
        "resume_phrases": ["hydraulics", "hydraulic"],
        "note": "Hydraulics coursework or project evidence is requested but not visible in the resume text.",
    },
    {
        "name": "Plant operations",
        "job_phrases": ["plant operations", "daily operations", "regular operation", "plant start-up", "plant shutdown", "operation unit", "shift"],
        "resume_phrases": ["plant operations", "daily operations", "regular operation", "plant start-up", "plant shutdown", "shift support"],
        "note": "Plant operations exposure appears adjacent, but direct operating-unit responsibility is not clearly shown.",
    },
    {
        "name": "Safety compliance",
        "job_phrases": ["safety", "health", "security", "ppe", "safe operation"],
        "resume_phrases": ["safety", "health", "security", "ppe"],
        "note": "Safety compliance responsibility is requested and is not clearly shown.",
    },
    {
        "name": "Regulatory or agency reporting",
        "job_phrases": ["agency reports", "regulatory reporting", "compliance reports", "permit", "permitting"],
        "resume_phrases": ["agency report", "agency reports", "regulatory report", "regulatory reporting", "permit reporting"],
        "note": "Regulatory or agency reporting is requested; the resume shows technical reporting/compliance adjacency but not clear reporting ownership.",
    },
    {
        "name": "Client presentations",
        "job_phrases": ["client presentations", "client presentation", "presentations"],
        "resume_phrases": ["client presentation", "client presentations", "presentations", "presented"],
        "note": "Presentation experience is relevant, but client-facing presentation ownership is not explicit.",
    },
    {
        "name": "Wastewater plant design",
        "job_phrases": ["wastewater treatment plant design", "plant design", "design projects", "process mechanical design"],
        "resume_phrases": ["plant design", "design projects", "process mechanical design", "developed patent-pending", "treatment selection"],
        "note": "Design-project or process-mechanical-design experience is requested and is not clearly shown as project delivery work.",
    },
]


def analyze_role_specific_gaps(job_text, resume_text):
    """Find practical JD requirements that are not clearly supported by the resume."""
    gaps = []

    for rule in ROLE_SPECIFIC_REQUIREMENT_RULES:
        if not any_phrase_found(rule["job_phrases"], job_text):
            continue
        if any_phrase_found(rule["resume_phrases"], resume_text):
            continue
        gaps.append(f"{rule['name']}: {rule['note']}")

    return gaps[:8]


def job_requests_keyword(keyword, job_text, trigger_map):
    """Check whether the job asks for a keyword or related trigger phrase."""
    if phrase_found_loose(keyword, job_text):
        return True
    return any_phrase_found(trigger_map.get(keyword, []), job_text)


def add_unique_note(notes, keyword, note):
    """Add one note per keyword so the tailoring section is not repetitive."""
    existing_keywords = {item.split(":", 1)[0].lower() for item in notes}
    if keyword.lower() not in existing_keywords:
        notes.append(note)


def tailoring_note_keyword(note):
    """Return the keyword part from a tailoring note."""
    return clean_keyword(note.split(":", 1)[0])


def is_water_consulting_tailoring_context(job_type, job_text):
    """Return True for water, wastewater, environmental, or consulting roles."""
    role_signals = ["wastewater", "water treatment", "environmental", "consult"]
    job_signals = ["wastewater", "water treatment", "environmental consulting", "consulting engineer", "consulting engineering"]
    return any(role_name_has(job_type, signal) for signal in role_signals) or any_phrase_found(job_signals, job_text)


def is_process_manufacturing_tailoring_context(job_type, job_text):
    """Return True when process/manufacturing language should drive priorities."""
    return role_name_has(job_type, "process engineer") or any_phrase_found(MANUFACTURING_SUPPORT_JOB_SIGNALS, job_text)


def job_clearly_requests_manufacturing_support(job_text):
    """Check whether manufacturing support wording is justified by the JD."""
    return any_phrase_found(MANUFACTURING_SUPPORT_JOB_SIGNALS, job_text)


def should_include_tailoring_keyword(keyword, job_text, job_type):
    """Apply role-specific filters without changing scoring."""
    normalized = clean_keyword(keyword)
    if normalized == "manufacturing support" and is_water_consulting_tailoring_context(job_type, job_text):
        return job_clearly_requests_manufacturing_support(job_text)
    return True


def sort_tailoring_notes_for_role(notes, job_text, job_type):
    """Order tailoring notes so the most role-specific items appear first."""
    if is_water_consulting_tailoring_context(job_type, job_text):
        priority_order = WATER_CONSULTING_PRIORITY_ORDER
    elif is_process_manufacturing_tailoring_context(job_type, job_text):
        priority_order = PROCESS_MANUFACTURING_PRIORITY_ORDER
    else:
        return notes

    order = {clean_keyword(keyword): index for index, keyword in enumerate(priority_order)}
    return sorted(
        notes,
        key=lambda note: (order.get(tailoring_note_keyword(note), len(order)), notes.index(note)),
    )


def classify_tailoring_priorities(missing_critical, missing_normal, job_text, resume_text, synonyms, job_type=""):
    """
    Classify important missing JD terms into practical tailoring groups.

    Rule 1: Good to emphasize
    The job asks for the term, the exact wording is not clearly present in the
    resume, but the resume contains related evidence.

    Rule 2: Transferable but needs careful wording
    The job asks for the term, and the resume suggests adjacent experience.
    These should be worded cautiously.

    Rule 3: Do not add unless true
    The job asks for the term, and the resume does not show enough support.
    These should not be forced into the resume.
    """
    good_to_emphasize = []
    transferable = []
    do_not_add = []
    missing_keywords = missing_critical + missing_normal
    profile = get_role_profile(job_type)
    profile_priority_skills = profile_list(profile, "priority_skills")
    profile_transferable_skills = profile_list(profile, "transferable_engineering_skills")

    # First classify controlled missing keywords from critical/normal lists.
    for keyword in missing_keywords:
        if not should_include_tailoring_keyword(keyword, job_text, job_type):
            continue
        if keyword in GOOD_TO_EMPHASIZE_RULES and any_phrase_found(GOOD_TO_EMPHASIZE_RULES[keyword], resume_text):
            add_unique_note(
                good_to_emphasize,
                keyword,
                f"{keyword}: Good to emphasize because the resume shows related evidence, but the job wording is not explicit.",
            )
        elif keyword in TRANSFERABLE_TAILORING_RULES and any_phrase_found(TRANSFERABLE_TAILORING_RULES[keyword], resume_text):
            add_unique_note(
                transferable,
                keyword,
                f"{keyword}: Transferable because the resume suggests related work, but the wording should stay cautious.",
            )
        else:
            add_unique_note(
                do_not_add,
                keyword,
                f"{keyword}: Do not add unless true because the current resume does not clearly support this wording.",
            )

    # Then scan for practical JD terms that may not be in the controlled keyword files.
    for keyword, evidence_phrases in GOOD_TO_EMPHASIZE_RULES.items():
        if not should_include_tailoring_keyword(keyword, job_text, job_type):
            continue
        if job_requests_keyword(keyword, job_text, GOOD_TO_EMPHASIZE_JOB_TRIGGERS) and not semantic_keyword_match(keyword, resume_text, synonyms)["matched"]:
            if any_phrase_found(evidence_phrases, resume_text):
                add_unique_note(
                    good_to_emphasize,
                    keyword,
                    f"{keyword}: Good to emphasize because related treatment, data, or chemistry evidence is already present.",
                )

    for keyword, evidence_phrases in TRANSFERABLE_TAILORING_RULES.items():
        if not should_include_tailoring_keyword(keyword, job_text, job_type):
            continue
        if job_requests_keyword(keyword, job_text, TRANSFERABLE_JOB_TRIGGERS) and not semantic_keyword_match(keyword, resume_text, synonyms)["matched"]:
            if any_phrase_found(evidence_phrases, resume_text):
                add_unique_note(
                    transferable,
                    keyword,
                    f"{keyword}: Transferable but needs careful wording because the resume shows adjacent experience, not direct role ownership.",
                )

    for skill in profile_priority_skills:
        if not should_include_tailoring_keyword(skill, job_text, job_type):
            continue
        if semantic_keyword_match(skill, job_text, synonyms)["matched"] and not semantic_keyword_match(skill, resume_text, synonyms)["matched"]:
            if any_phrase_found(profile_transferable_skills, resume_text):
                add_unique_note(
                    transferable,
                    skill,
                    f"{skill}: Important for the {job_type} profile; use adjacent experience only if the wording stays truthful.",
                )
            else:
                add_unique_note(
                    do_not_add,
                    skill,
                    f"{skill}: Important for the {job_type} profile, but the current resume does not clearly support it.",
                )

    for skill in profile_transferable_skills:
        if not should_include_tailoring_keyword(skill, job_text, job_type):
            continue
        if semantic_keyword_match(skill, resume_text, synonyms)["matched"] and not semantic_keyword_match(skill, job_text, synonyms)["matched"]:
            add_unique_note(
                good_to_emphasize,
                skill,
                f"{skill}: Transferable strength from the {job_type} profile that may help if connected to the JD's wording.",
            )

    for keyword, job_phrases in DO_NOT_ADD_RULES.items():
        if any_phrase_found(job_phrases, job_text) and not any_phrase_found(job_phrases, resume_text):
            add_unique_note(
                do_not_add,
                keyword,
                f"{keyword}: Do not add unless true because this is a specific tool, duty, or regulated work area not shown in the resume.",
            )

    return {
        "good_to_emphasize": sort_tailoring_notes_for_role(good_to_emphasize, job_text, job_type),
        "transferable": sort_tailoring_notes_for_role(transferable, job_text, job_type),
        "do_not_add": do_not_add,
    }


# ------------------------------------------------------------
# Tone and ATS readability
# ------------------------------------------------------------


def analyze_industry_tone(resume_text, job_type):
    """Find academic wording and suggest industry-oriented alternatives."""
    findings = []
    lower_resume = resume_text.lower()
    academic_level = role_academic_level(job_type)

    if academic_level == "high" or job_type == "R&D scientist":
        allowed_words = {"investigated", "studied", "characterized", "examined"}
    elif academic_level == "moderate":
        allowed_words = {"characterized"}
    else:
        allowed_words = set()

    for academic_word, industry_word in ACADEMIC_WORDS.items():
        if academic_word in allowed_words:
            continue
        if academic_word in lower_resume:
            findings.append(
                f"Consider replacing '{academic_word}' with '{industry_word}' when the meaning stays accurate."
            )

    if not findings:
        if academic_level == "high":
            findings.append("Academic wording is acceptable for this role family when it is tied to methods, results, treatment performance, or applied impact.")
        elif academic_level == "moderate":
            findings.append("Academic wording is acceptable in moderation, but the strongest bullets should still connect to practical engineering outcomes.")
        else:
            findings.append("No major academic wording patterns were detected.")

    return findings[:6]


def calculate_ats_readability(bullets, resume_keywords):
    """Create a qualitative ATS/readability assessment."""
    if not bullets:
        return {
            "assessment": "Needs improvement",
            "average_bullet_length": 0,
            "action_verb_rate": 0,
            "acronym_density": 0,
            "long_bullets": 0,
            "suggestions": ["Add clear bullet points with action verbs and measurable technical outcomes."],
        }

    bullet_word_counts = [len(get_words(bullet)) for bullet in bullets]
    total_words = sum(bullet_word_counts)
    average_length = round(total_words / len(bullets), 1)

    action_starts = 0
    for bullet in bullets:
        if get_bullet_action_verb(bullet) in ACTION_VERBS:
            action_starts += 1

    action_verb_rate = round((action_starts / len(bullets)) * 100)
    keyword_hits = sum(1 for keyword in resume_keywords if keyword_found_in_text(keyword, " ".join(bullets)))

    acronym_count = len(re.findall(r"\b[A-Z]{2,}\b", " ".join(bullets)))
    acronym_density = round((acronym_count / max(total_words, 1)) * 100, 1)
    long_bullets = sum(1 for count in bullet_word_counts if count > 35)

    issue_count = 0
    suggestions = []

    if average_length > 28:
        issue_count += 1
        suggestions.append("Shorten long bullets so technical points are easier to scan.")
    if action_verb_rate < 50:
        issue_count += 1
        suggestions.append("Start more bullets with clear action verbs such as evaluated, optimized, supported, or developed.")
    if keyword_hits < 3:
        issue_count += 1
        suggestions.append("Add relevant target keywords where they accurately describe your work.")
    if acronym_density > 8:
        issue_count += 1
        suggestions.append("Define or reduce acronyms if bullets feel too dense.")
    if long_bullets:
        issue_count += 1
        suggestions.append("Split excessively long bullets into shorter, outcome-focused statements.")

    if not suggestions:
        suggestions.append("Readable and ATS-friendly overall; keep bullets concise, action-oriented, and tied to real role keywords.")

    if issue_count == 0:
        assessment = "Strong"
    elif issue_count <= 2:
        assessment = "Moderate"
    else:
        assessment = "Needs improvement"

    return {
        "assessment": assessment,
        "average_bullet_length": average_length,
        "action_verb_rate": action_verb_rate,
        "acronym_density": acronym_density,
        "long_bullets": long_bullets,
        "suggestions": suggestions[:5],
    }


def create_semantic_match_notes(matched_keywords, job_match_details, resume_match_details):
    """Create short notes for partial semantic matches."""
    notes = []

    for keyword in matched_keywords:
        job_match = job_match_details.get(keyword, {})
        resume_match = resume_match_details.get(keyword, {})

        job_type = job_match.get("match_type", "exact")
        resume_type = resume_match.get("match_type", "exact")

        note_parts = []
        if job_type != "exact" and job_match.get("evidence"):
            note_parts.append(f"job text matched through '{job_match['evidence']}' ({job_type})")
        if resume_type != "exact" and resume_match.get("evidence"):
            note_parts.append(f"resume matched through '{resume_match['evidence']}' ({resume_type})")

        if note_parts:
            notes.append(f"{keyword}: " + "; ".join(note_parts) + ".")

    return notes


# ------------------------------------------------------------
# Report text helpers
# ------------------------------------------------------------


def bullet_list(items, empty_message):
    """Format a plain Markdown bullet list."""
    if not items:
        return f"- {empty_message}"
    return "\n".join(f"- {item}" for item in items)


TRANSFERABLE_DISPLAY_OVERLAPS = [
    {"data interpretation", "data analysis"},
    {"treatment performance", "treatment performance evaluation"},
]


def display_transferable_skills(skills, limit=3):
    """Return a concise, display-only list of transferable skills."""
    selected = []
    seen = set()

    for skill in skills:
        normalized = clean_keyword(skill)
        if normalized in seen:
            continue
        if any(normalized in group and any(clean_keyword(item) in group for item in selected) for group in TRANSFERABLE_DISPLAY_OVERLAPS):
            continue

        selected.append(skill)
        seen.add(normalized)

        if len(selected) == limit:
            break

    return selected


def bullet_analysis_list(items, empty_message):
    """Format bullet relevance findings."""
    if not items:
        return f"- {empty_message}"

    lines = []
    for item in items:
        direct = ", ".join(item["matched"]) if item["matched"] else "none"
        displayed_transferable = display_transferable_skills(item.get("transferable", []))
        transferable = ", ".join(displayed_transferable) if displayed_transferable else "none"
        lines.append(
            f"- {item['text']}  \n  Match type: {item.get('match_type', 'Low relevance')}. Direct keywords: {direct}. Transferable skills: {transferable}. Reason: {item.get('reason', 'Review manually.')}"
        )
    return "\n".join(lines)


def create_resume_strengths(matched_critical, matched_normal, strongest_bullets):
    """Create concise resume strength notes."""
    strengths = []

    if matched_critical:
        strengths.append("The resume already supports critical industry terms: " + ", ".join(matched_critical) + ".")
    if matched_normal:
        strengths.append("The resume also matches normal target terms: " + ", ".join(matched_normal) + ".")
    if strongest_bullets:
        strengths.append("Several resume bullets connect directly to job keywords and should be easy for a reviewer to recognize.")

    return strengths or ["The resume has limited direct keyword overlap with this posting."]


def has_any_keyword(text, keywords, synonyms):
    """Return True if any keyword appears exactly or semantically in text."""
    for keyword in keywords:
        if semantic_keyword_match(keyword, text, synonyms)["matched"]:
            return True
    return False


def create_resume_differentiation_analysis(resume_text, job_text, matched_keywords, job_type, synonyms):
    """
    Identify realistic differentiators in the resume.

    These are not claims that the candidate is superior. They are grounded notes
    about uncommon or useful combinations that may help the resume stand out.
    """
    analysis = []
    matched_set = {clean_keyword(keyword) for keyword in matched_keywords}
    water_related_job = is_water_treatment_related_job(job_text)

    has_upw = has_any_keyword(resume_text, ["UPW", "ultrapure water"], synonyms)
    has_aop = has_any_keyword(resume_text, ["AOP", "advanced oxidation", "ozone", "UV"], synonyms)
    has_semiconductor = has_any_keyword(resume_text + "\n" + job_text, ["semiconductor"], synonyms)
    has_kinetics = has_any_keyword(resume_text, ["reaction kinetics"], synonyms)
    has_engineering = has_any_keyword(
        resume_text,
        ["process engineering", "environmental engineering", "water treatment", "treatment performance"],
        synonyms,
    )
    has_ozone = has_any_keyword(resume_text, ["ozone"], synonyms)
    has_bromine = has_any_keyword(resume_text, ["bromine", "bromide", "bromate"], synonyms)
    has_data = has_any_keyword(resume_text, ["data interpretation", "data analysis"], synonyms)
    has_byproduct = has_any_keyword(resume_text, ["byproduct control"], synonyms) or has_bromine

    if water_related_job and has_upw and has_aop:
        analysis.append(
            "Unique technical strength: UPW exposure combined with advanced oxidation, ozone, or UV treatment experience."
        )

    if water_related_job and has_upw and has_semiconductor:
        analysis.append(
            "Niche industry relevance: UPW background can be positioned toward semiconductor or high-purity water environments if supported by the resume."
        )
    elif water_related_job and has_upw and role_name_has(job_type, "UPW"):
        analysis.append(
            "Niche industry relevance: UPW background is directly relevant for high-purity water roles."
        )

    if water_related_job and has_kinetics and has_engineering:
        analysis.append(
            "Differentiating combination: mechanistic chemistry or reaction kinetics paired with applied water treatment engineering context."
        )

    if water_related_job and has_ozone and has_bromine:
        analysis.append(
            "Uncommon expertise: ozone-related chemistry with bromine, bromide, or bromate awareness may be valuable for byproduct-sensitive treatment work."
        )

    if water_related_job and has_data and has_engineering:
        analysis.append(
            "Practical strength: data interpretation connected to treatment performance, troubleshooting, or engineering decisions."
        )

    if "wastewater" in matched_set and has_data:
        analysis.append(
            "Role-relevant combination: wastewater familiarity plus technical data analysis is useful for consulting, compliance, and design-support roles."
        )

    if not water_related_job and has_data:
        analysis.append(
            "Transferable strength: technical data interpretation can support troubleshooting, reporting, and engineering decisions if rewritten in the job's operating context."
        )

    if not water_related_job and has_any_keyword(resume_text, ["technical reporting", "troubleshooting"], synonyms):
        analysis.append(
            "Practical overlap: the resume shows reporting or troubleshooting signals that can be tailored toward plant, process, or project-support language."
        )

    if not analysis:
        analysis.append(
            "No strong niche differentiator was detected from the current keyword lists; emphasize only the most relevant evidence for this specific job."
        )

    return analysis[:5]


def choose_engineering_identity(job_type, matched_keywords, resume_text, synonyms, job_text=""):
    """Choose a realistic engineering identity for this specific job."""
    matched_set = {clean_keyword(keyword) for keyword in matched_keywords}
    water_related_job = is_water_treatment_related_job(job_text)
    has_upw = has_any_keyword(resume_text, ["UPW", "ultrapure water"], synonyms)
    has_aop = has_any_keyword(resume_text, ["AOP", "advanced oxidation", "ozone", "UV"], synonyms)
    has_environmental = "environmental engineering" in matched_set or "wastewater" in matched_set
    has_process = has_any_keyword(resume_text, ["process engineering", "process optimization", "treatment performance"], synonyms)

    if role_name_has(job_type, "wastewater"):
        return "wastewater treatment engineer"
    if (role_name_has(job_type, "environmental") or role_name_has(job_type, "consult")) and has_environmental:
        return "environmental process engineer"
    if role_name_has(job_type, "water treatment") or "water treatment" in matched_set:
        return "water treatment engineer"
    if role_name_has(job_type, "process engineer") and not water_related_job:
        return "process engineering candidate with transferable water/industrial wastewater background"
    if role_name_has(job_type, "process engineer"):
        return "process-oriented water treatment engineer"
    if role_name_has(job_type, "UPW") or (has_upw and "process optimization" in matched_set):
        return "UPW/process engineer"
    if role_name_has(job_type, "R&D") or (has_aop and has_process):
        return "applied R&D engineer"
    return "water treatment / environmental engineering candidate"


def identify_positioning_angle(job_type, matched_keywords, resume_text, synonyms, job_text=""):
    """Identify the strongest positioning angle for the job."""
    matched_set = {clean_keyword(keyword) for keyword in matched_keywords}
    water_related_job = is_water_treatment_related_job(job_text)
    has_upw = has_any_keyword(resume_text, ["UPW", "ultrapure water"], synonyms)
    has_aop = has_any_keyword(resume_text, ["AOP", "advanced oxidation", "ozone", "UV"], synonyms)
    has_data = has_any_keyword(resume_text, ["data interpretation", "data analysis"], synonyms)
    has_kinetics = has_any_keyword(resume_text, ["reaction kinetics"], synonyms)

    if role_name_has(job_type, "wastewater"):
        return "Position around wastewater treatment performance, process evaluation, technical reporting, and the JD's design/modeling requirements."
    if (role_name_has(job_type, "consult") or role_name_has(job_type, "environmental consultant")) and ("wastewater" in matched_set or has_data):
        return "Position as a treatment-focused engineer who can turn water quality data into practical consulting or design-support insights."
    if role_name_has(job_type, "process engineer") and not water_related_job:
        return "Position as a technical process candidate with transferable troubleshooting, data interpretation, reporting, and industrial wastewater exposure."
    if role_name_has(job_type, "process engineer") and (has_upw or "process optimization" in matched_set):
        return "Position as a process-oriented engineer with treatment performance, troubleshooting, and optimization relevance."
    if role_name_has(job_type, "UPW") and has_upw:
        return "Position as a UPW-focused engineer with high-purity water and advanced treatment relevance."
    if role_name_has(job_type, "R&D") and (has_aop or has_kinetics):
        return "Position as an applied R&D engineer who connects treatment chemistry to practical water quality outcomes."
    if "water treatment" in matched_set:
        return "Position around applied water treatment performance and technical data interpretation."
    return "Position around the most relevant water treatment, chemistry, and data interpretation evidence for this role."


def identify_positioning_strengths(matched_keywords, resume_text, synonyms, job_text=""):
    """Identify strengths to emphasize for strategic positioning."""
    strengths = []
    water_related_job = is_water_treatment_related_job(job_text)

    if not water_related_job:
        if has_any_keyword(resume_text, ["data interpretation", "data analysis"], synonyms):
            strengths.append("technical data interpretation")
        if has_any_keyword(resume_text, ["troubleshooting"], synonyms):
            strengths.append("process troubleshooting")
        if has_any_keyword(resume_text, ["technical reporting"], synonyms):
            strengths.append("technical reporting")
        if has_any_keyword(resume_text, ["wastewater"], synonyms):
            strengths.append("transferable industrial wastewater project exposure")
        if matched_keywords:
            strengths.append("direct overlap with role keywords: " + ", ".join(matched_keywords[:4]))
        return strengths[:5] or ["Most relevant process, data, reporting, and troubleshooting evidence in the resume"]

    if has_any_keyword(resume_text, ["UPW", "ultrapure water"], synonyms):
        strengths.append("UPW or high-purity water exposure")
    if has_any_keyword(resume_text, ["AOP", "advanced oxidation", "ozone", "UV"], synonyms):
        strengths.append("advanced oxidation, ozone, or UV treatment experience")
    if has_any_keyword(resume_text, ["reaction kinetics"], synonyms):
        strengths.append("reaction kinetics and treatment chemistry interpretation")
    if has_any_keyword(resume_text, ["byproduct control"], synonyms) or has_any_keyword(resume_text, ["bromine", "bromide", "bromate"], synonyms):
        strengths.append("byproduct-aware water chemistry")
    if has_any_keyword(resume_text, ["data interpretation", "data analysis"], synonyms):
        strengths.append("water quality data interpretation")
    if matched_keywords:
        strengths.append("direct overlap with role keywords: " + ", ".join(matched_keywords[:4]))

    return strengths[:5] or ["Most relevant treatment and data evidence in the resume"]


def identify_academic_or_detailed_experience(resume_text, job_type):
    """Flag experience that may need less emphasis for industry positioning."""
    flags = []
    lower_resume = resume_text.lower()

    academic_terms = ["publication", "mechanistic", "investigated", "studied", "elucidated"]
    if role_academic_level(job_type) != "high":
        for term in academic_terms:
            if term in lower_resume:
                flags.append(
                    f"'{term}' language may be too academic unless tied to engineering decisions or treatment outcomes."
                )

    if "reaction kinetics" in lower_resume and role_academic_level(job_type) != "high":
        flags.append(
            "Detailed reaction-kinetics discussion should be kept practical and connected to treatment performance."
        )

    if "publication" in lower_resume and role_academic_level(job_type) != "high":
        flags.append(
            "Publications can support credibility, but they should not crowd out applied project, testing, or engineering evidence."
        )

    return flags[:4] or ["No major academic-overdetail concern was detected for this job type."]


def create_strategic_positioning_analysis(job_type, matched_keywords, resume_text, synonyms, job_text=""):
    """Create strategic resume positioning guidance without rewriting the resume."""
    identity = choose_engineering_identity(job_type, matched_keywords, resume_text, synonyms, job_text)

    return {
        "angle": identify_positioning_angle(job_type, matched_keywords, resume_text, synonyms, job_text),
        "strengths": identify_positioning_strengths(matched_keywords, resume_text, synonyms, job_text),
        "too_academic": identify_academic_or_detailed_experience(resume_text, job_type),
        "identity": identity,
    }


def create_professional_summary_suggestion(job_type, matched_keywords, resume_text, synonyms, job_text=""):
    """
    Create a concise professional summary suggestion.

    The wording uses only supported signals found in the resume and adapts the
    emphasis to the detected job type.
    """
    identity = choose_engineering_identity(job_type, matched_keywords, resume_text, synonyms, job_text)
    strengths = identify_positioning_strengths(matched_keywords, resume_text, synonyms, job_text)
    water_related_job = is_water_treatment_related_job(job_text)

    has_upw = has_any_keyword(resume_text, ["UPW", "ultrapure water"], synonyms)
    has_aop = has_any_keyword(resume_text, ["AOP", "advanced oxidation", "ozone", "UV"], synonyms)
    has_kinetics = has_any_keyword(resume_text, ["reaction kinetics"], synonyms)
    has_data = has_any_keyword(resume_text, ["data interpretation", "data analysis"], synonyms)
    has_wastewater = has_any_keyword(resume_text, ["wastewater"], synonyms)
    has_water_quality = has_any_keyword(resume_text, ["water quality"], synonyms)

    sentences = []
    if " with " in identity:
        sentences.append(
            f"{identity.capitalize()}, bringing experience in " + format_summary_strengths(strengths[:3]) + "."
        )
    else:
        sentences.append(
            f"{identity.capitalize()} with experience in " + format_summary_strengths(strengths[:3]) + "."
        )

    if role_name_has(job_type, "wastewater"):
        if has_data or has_water_quality:
            sentences.append(
                "Brings water quality data interpretation and treatment performance evaluation experience that can support wastewater process analysis."
            )
        sentences.append(
            "Tailoring should address the JD's specific design, modeling, hydraulics, and deliverable requirements only where supported."
        )
    elif role_name_has(job_type, "consult"):
        if has_data or has_water_quality:
            sentences.append(
                "Brings water quality data interpretation and treatment performance evaluation experience to support practical engineering decisions."
            )
        if has_wastewater:
            sentences.append(
                "Relevant background includes wastewater and environmental treatment work suited to consulting, compliance, or design-support projects."
            )
    elif role_name_has(job_type, "process engineer"):
        if water_related_job:
            sentences.append(
                "Offers treatment-process experience that can be positioned around performance evaluation, troubleshooting, and practical optimization."
            )
        else:
            sentences.append(
                "Offers transferable process-analysis experience that can be positioned around troubleshooting, quality, reporting, and practical optimization."
            )
    elif role_name_has(job_type, "UPW"):
        if has_upw:
            sentences.append(
                "Relevant background includes UPW or high-purity water exposure with attention to trace contaminant control and water quality."
            )
    elif role_name_has(job_type, "R&D"):
        if has_aop or has_kinetics:
            sentences.append(
                "Connects advanced treatment chemistry, reaction kinetics, and experimental evaluation to applied water treatment outcomes."
            )
    else:
        sentences.append(
            "Brings a water treatment background with emphasis on technical analysis, treatment performance, and practical problem solving."
        )

    if has_aop and has_data and water_related_job and len(sentences) < 4:
        sentences.append(
            "Strengths include interpreting treatment data from advanced oxidation, ozone, UV, or related water chemistry work."
        )

    return " ".join(sentences[:4])


def format_summary_strengths(strengths):
    """Format strengths for one professional-summary sentence."""
    cleaned = []
    phrase_map = {
        "UPW or high-purity water exposure": "UPW and high-purity water",
        "advanced oxidation, ozone, or UV treatment experience": "advanced oxidation, ozone, and UV treatment",
        "reaction kinetics and treatment chemistry interpretation": "reaction kinetics and treatment chemistry",
        "byproduct-aware water chemistry": "byproduct-aware water chemistry",
        "water quality data interpretation": "water quality data interpretation",
    }

    for strength in strengths:
        if strength.startswith("direct overlap with role keywords:"):
            continue
        cleaned.append(phrase_map.get(strength, strength))

    if not cleaned:
        return "water treatment, technical analysis, and treatment performance evaluation"
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return cleaned[0] + " and " + cleaned[1]
    return cleaned[0] + ", " + cleaned[1] + ", and " + cleaned[2]


def create_resume_weaknesses(missing_critical, missing_normal, weak_bullets, job_text=""):
    """Create concise resume weakness notes."""
    weaknesses = []

    if missing_critical:
        weaknesses.append("Critical keywords are missing or not visible: " + ", ".join(missing_critical) + ".")
    if missing_normal:
        weaknesses.append("Normal target keywords are missing: " + ", ".join(missing_normal) + ".")
    if weak_bullets and is_water_treatment_related_job(job_text):
        weaknesses.append("Some bullets appear less relevant to this job and may distract from stronger water treatment or UPW evidence.")
    elif weak_bullets:
        weaknesses.append("Some bullets appear less relevant to this job; prioritize the most transferable process, reporting, troubleshooting, or operations evidence.")

    return weaknesses or ["No major keyword weaknesses were found from the current target lists."]


def explain_keyword_value(keyword):
    """Explain why a missing keyword may matter."""
    keyword_lower = clean_keyword(keyword)

    explanations = {
        "upw": "Signals direct relevance to ultrapure water systems and high-purity water environments.",
        "ultrapure water": "Signals direct relevance to high-purity water systems and semiconductor-style water quality demands.",
        "ro": "Shows familiarity with membrane treatment, a common unit process in advanced water systems.",
        "reverse osmosis": "Shows familiarity with membrane treatment, a common unit process in advanced water systems.",
        "semiconductor": "Connects the resume to high-purity manufacturing environments where UPW is especially important.",
        "pilot testing": "Shows ability to evaluate treatment ideas before full-scale implementation.",
        "process optimization": "Shows practical focus on improving treatment conditions, performance, or operations.",
        "process control": "Signals operational awareness and ability to keep treatment processes stable.",
        "process engineering": "Connects technical work to applied engineering design, operation, and improvement.",
        "water treatment": "Establishes core relevance to the role's treatment-process focus.",
        "wastewater": "Shows fit for treatment, compliance, and environmental engineering work.",
        "ozone": "Highlights advanced oxidation or disinfection experience relevant to treatment performance.",
        "uv": "Highlights photolysis, disinfection, or AOP experience relevant to advanced treatment.",
        "aop": "Connects directly to advanced oxidation treatment and contaminant control.",
        "advanced oxidation": "Connects directly to advanced treatment chemistry and contaminant control.",
        "reaction kinetics": "Shows ability to interpret treatment rates, oxidant demand, and process behavior.",
        "byproduct control": "Shows awareness of treatment side effects and finished-water quality risks.",
        "contaminant removal": "Connects technical work to practical treatment outcomes.",
        "water quality": "Shows ability to evaluate treatment performance using practical quality indicators.",
        "data interpretation": "Shows ability to convert technical data into engineering conclusions.",
        "data analysis": "Shows ability to evaluate datasets and support technical decisions.",
        "technical reporting": "Matters for documenting results, recommendations, and engineering decisions.",
        "troubleshooting": "Signals practical problem-solving for operations, testing, or project support.",
        "laboratory analysis": "Shows hands-on technical testing and measurement experience.",
        "environmental engineering": "Signals broad fit for environmental treatment, compliance, and water projects.",
        "treatment performance": "Connects resume evidence to measurable treatment outcomes.",
    }

    return explanations.get(keyword_lower, "This term may help connect the resume more directly to the job description.")


def estimate_missing_keyword_importance(keyword, job_type, is_critical):
    """Estimate whether a missing keyword is high, medium, or low importance."""
    priority_keywords = {clean_keyword(item) for item in get_job_type_priority_keywords(job_type)}
    keyword_lower = clean_keyword(keyword)

    if is_critical or keyword_lower in priority_keywords:
        return "high"
    if keyword in TRANSFERABLE_KEYWORDS or keyword in SAFE_TO_EMPHASIZE:
        return "medium"
    return "low"


def classify_missing_keyword_need(importance, is_critical):
    """Classify a missing keyword as likely critical or optional."""
    if is_critical or importance == "high":
        return "likely critical"
    if importance == "medium":
        return "role-supporting"
    return "optional"


def create_missing_keyword_notes(missing_keywords, job_type, is_critical):
    """Create concise notes for missing keywords."""
    notes = []

    for keyword in missing_keywords:
        importance = estimate_missing_keyword_importance(keyword, job_type, is_critical)
        need = classify_missing_keyword_need(importance, is_critical)
        why_it_matters = explain_keyword_value(keyword)
        notes.append(
            f"{keyword}: {why_it_matters} Importance for this role: {importance}; {need}."
        )

    return notes


def create_recommended_focus(safe, transferable, unsupported, missing_critical, job_type):
    """Create a short recommended focus list."""
    focus = []
    if any(role_name_has(job_type, signal) for signal in ["wastewater", "water treatment", "environmental", "consult"]):
        priority_keywords = WATER_CONSULTING_PRIORITY_ORDER
    else:
        priority_keywords = get_job_type_priority_keywords(job_type)

    if priority_keywords:
        focus.append(f"For this {job_type} role, prioritize: " + ", ".join(priority_keywords[:5]) + ".")

    if safe:
        focus.append("Lead with directly supported topics: " + ", ".join(note.split(":", 1)[0] for note in safe[:5]) + ".")
    if transferable:
        focus.append("Use transferable wording carefully for: " + ", ".join(note.split(":", 1)[0] for note in transferable[:5]) + ".")
    if missing_critical:
        focus.append("Address missing critical terms only if your real experience supports them.")
    if unsupported:
        focus.append("Do not force unsupported terms into the resume: " + ", ".join(note.split(":", 1)[0] for note in unsupported[:5]) + ".")

    return focus or ["Keep the resume focused on water treatment, UPW, AOPs, process data, and treatment performance."]


def create_markdown_report(data):
    """Build the final Markdown report."""
    ats = data["ats"]
    role_gaps = data["role_specific_gaps"] or data["role_priority_alignment"]["missing"]

    return f"""# Job Application Review

Job file: `{data['job_file']}`

## Overall Fit Assessment
- Detected role family: **{data['job_type']}**
- Fit category: **{data['fit_category']}** ({data['fit_score']}%)
- Domain alignment: **{data['domain_alignment']['label']}** ({data['domain_alignment']['score']}%)
- Recommendation: **{data['recommendation']}**
- Reason: {data['recommendation_reason']}
- ATS readability: **{ats['assessment']}**

## Role-Specific Gaps
{bullet_list(role_gaps, "No major role-specific gaps found from the current rule list.")}

## Strategic Resume Positioning
- Strongest positioning angle: {data['positioning']['angle']}
- Best-fit engineering identity: **{data['positioning']['identity']}**

Technical strengths to emphasize:
{bullet_list(data['positioning']['strengths'], "No specific strengths identified.")}

## Resume Bullet Relevance Analysis
Direct matches:
{bullet_analysis_list(data['strongest_bullets'], "No direct bullet matches found.")}

Transferable matches:
{bullet_analysis_list(data['transferable_bullets'], "No transferable bullet matches found.")}

Low relevance:
{bullet_analysis_list(data['low_relevance_bullets'], "No low-relevance bullets detected.")}

## Tailored Professional Summary Suggestion
{data['professional_summary']}

## Resume Tailoring Priorities
Good to emphasize:
{bullet_list(data['tailoring_priorities']['good_to_emphasize'], "None identified")}

Transferable but needs careful wording:
{bullet_list(data['tailoring_priorities']['transferable'], "None identified")}

Do not add unless true:
{bullet_list(data['tailoring_priorities']['do_not_add'], "None identified")}

## Recommended Resume Focus
{bullet_list(data['recommended_focus'], "Keep the resume focused on relevant water treatment evidence.")}
"""


# ------------------------------------------------------------
# Job review flow
# ------------------------------------------------------------


def create_output_file_path(job_file_path):
    """Create the output file path for one job report."""
    return OUTPUTS_DIR / f"{job_file_path.stem}_review.md"


def get_job_files():
    """Return all .txt files inside data/jobs."""
    return sorted(JOBS_DIR.glob("*.txt"))


def load_analysis_config():
    """Load keyword lists, synonyms, and role profiles used by both CLI and app."""
    target_keywords = load_keyword_file(
        TARGET_KEYWORDS_FILE,
        DEFAULT_TARGET_KEYWORDS,
        "target keyword file",
    )
    critical_keywords = load_keyword_file(
        CRITICAL_KEYWORDS_FILE,
        DEFAULT_CRITICAL_KEYWORDS,
        "critical keyword file",
    )
    synonyms = load_synonyms()
    role_profiles = load_role_profiles()
    normal_keywords = remove_keywords(target_keywords, critical_keywords)

    return {
        "target_keywords": target_keywords,
        "critical_keywords": critical_keywords,
        "normal_keywords": normal_keywords,
        "synonyms": synonyms,
        "role_profiles": role_profiles,
    }


def prepare_resume_context(resume_text, normal_keywords, critical_keywords, synonyms):
    """Prepare resume matches and sections once for one analysis run."""
    resume_sections = detect_resume_sections(resume_text)
    resume_bullets = detect_resume_bullets(resume_text)

    resume_critical_matches = find_keyword_matches(critical_keywords, resume_text, synonyms)
    resume_normal_matches = find_keyword_matches(normal_keywords, resume_text, synonyms)
    resume_critical = list(resume_critical_matches.keys())
    resume_normal = list(resume_normal_matches.keys())
    resume_match_details = {}
    resume_match_details.update(resume_critical_matches)
    resume_match_details.update(resume_normal_matches)
    keyword_sections = find_keyword_sections(
        resume_critical + resume_normal,
        resume_sections,
        synonyms,
    )

    return {
        "sections": resume_sections,
        "bullets": resume_bullets,
        "resume_normal": resume_normal,
        "resume_critical": resume_critical,
        "resume_match_details": resume_match_details,
        "keyword_sections": keyword_sections,
    }


def create_summary_row(report_data, report_file=""):
    """Create the summary row used by the CLI CSV output."""
    matched_keywords = report_data["matched_critical"] + report_data["matched_normal"]
    missing_keywords = report_data["missing_critical"] + report_data["missing_normal"]

    return {
        "job_file": report_data["job_file"],
        "job_type": report_data["job_type"],
        "fit_category": report_data["fit_category"],
        "match_rate": report_data["fit_score"],
        "matched_keywords": ", ".join(matched_keywords),
        "missing_keywords": ", ".join(missing_keywords),
        "recommendation": report_data["recommendation"],
        "report_file": report_file,
    }


def analyze_job_text(
    job_name,
    job_text,
    resume_text,
    resume_sections,
    resume_bullets,
    normal_keywords,
    critical_keywords,
    resume_normal,
    resume_critical,
    resume_match_details,
    keyword_sections,
    synonyms,
    role_profiles,
):
    """Review one job description text and return report data plus Markdown."""
    job_type, job_type_scores = detect_job_type(job_text, role_profiles)

    job_critical_matches = find_keyword_matches(critical_keywords, job_text, synonyms)
    job_normal_matches = find_keyword_matches(normal_keywords, job_text, synonyms)
    job_match_details = {}
    job_match_details.update(job_critical_matches)
    job_match_details.update(job_normal_matches)
    job_critical = list(job_critical_matches.keys())
    job_normal = list(job_normal_matches.keys())

    matched_critical = find_matched_keywords(job_critical, resume_critical)
    missing_critical = find_missing_keywords(job_critical, resume_critical)
    matched_normal = find_matched_keywords(job_normal, resume_normal)
    missing_normal = find_missing_keywords(job_normal, resume_normal)

    all_job_keywords = job_critical + job_normal
    all_missing = missing_critical + missing_normal
    all_resume_keywords = resume_critical + resume_normal

    keyword_fit_score = calculate_weighted_fit_score(
        job_critical,
        job_normal,
        matched_critical,
        matched_normal,
        keyword_sections,
        resume_match_details,
    )
    keyword_fit_score = adjust_score_for_job_type(
        keyword_fit_score,
        job_type,
        all_job_keywords,
        matched_critical + matched_normal,
        job_text,
        resume_text,
        synonyms,
    )
    role_profile_score = calculate_role_profile_fit_score(job_type, job_text, resume_text, synonyms)
    domain_alignment = calculate_domain_alignment_score(job_text, resume_text, synonyms)
    domain_alignment["label"] = choose_domain_alignment_label(domain_alignment["score"])
    fit_score = combine_fit_scores(
        keyword_fit_score,
        role_profile_score,
        domain_alignment["score"],
        len(job_critical) + len(job_normal),
    )
    role_priority_alignment = analyze_role_specific_priorities(
        job_type,
        job_text,
        resume_text,
        synonyms,
    )
    fit_score = adjust_score_for_role_priorities(fit_score, role_priority_alignment)
    role_specific_gaps = analyze_role_specific_gaps(job_text, resume_text)
    displayed_role_profile_score = adjust_score_for_role_specific_gaps(role_profile_score, role_specific_gaps)
    fit_score = adjust_score_for_role_specific_gaps(fit_score, role_specific_gaps)
    fit_category = choose_fit_category(fit_score)

    strongest, weak, move_earlier = analyze_resume_bullets(
        resume_text,
        resume_sections,
        all_job_keywords,
        critical_keywords,
        synonyms,
        job_text,
        job_type,
    )
    tone_findings = analyze_industry_tone(resume_text, job_type)
    ats = calculate_ats_readability(resume_bullets, all_resume_keywords)
    tailoring_priorities = classify_tailoring_priorities(
        missing_critical,
        missing_normal,
        job_text,
        resume_text,
        synonyms,
        job_type,
    )
    recommendation, recommendation_reason = create_application_recommendation(
        fit_score,
        missing_critical,
        missing_normal,
        len(job_critical) + len(job_normal),
        role_priority_alignment,
        role_specific_gaps,
        job_type,
    )

    report_data = {
        "job_file": job_name,
        "job_type": job_type,
        "job_type_notes": create_job_type_notes(job_type),
        "role_priority_alignment": role_priority_alignment,
        "fit_score": fit_score,
        "domain_alignment": domain_alignment,
        "keyword_fit_score": keyword_fit_score,
        "role_profile_score": displayed_role_profile_score,
        "fit_category": fit_category,
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
        "matched_critical": matched_critical,
        "missing_critical": missing_critical,
        "missing_critical_notes": create_missing_keyword_notes(
            missing_critical,
            job_type,
            True,
        ),
        "matched_normal": matched_normal,
        "missing_normal": missing_normal,
        "missing_normal_notes": create_missing_keyword_notes(
            missing_normal,
            job_type,
            False,
        ),
        "semantic_notes": create_semantic_match_notes(
            matched_critical + matched_normal,
            job_match_details,
            resume_match_details,
        ),
        "strengths": create_resume_strengths(matched_critical, matched_normal, strongest),
        "differentiation": create_resume_differentiation_analysis(
            resume_text,
            job_text,
            matched_critical + matched_normal,
            job_type,
            synonyms,
        ),
        "role_specific_gaps": role_specific_gaps,
        "positioning": create_strategic_positioning_analysis(
            job_type,
            matched_critical + matched_normal,
            resume_text,
            synonyms,
            job_text,
        ),
        "professional_summary": create_professional_summary_suggestion(
            job_type,
            matched_critical + matched_normal,
            resume_text,
            synonyms,
            job_text,
        ),
        "weaknesses": create_resume_weaknesses(missing_critical, missing_normal, weak, job_text),
        "strongest_bullets": strongest,
        "transferable_bullets": weak,
        "low_relevance_bullets": move_earlier,
        "tone_findings": tone_findings,
        "ats": ats,
        "tailoring_priorities": tailoring_priorities,
        "recommended_focus": create_recommended_focus(
            tailoring_priorities["good_to_emphasize"],
            tailoring_priorities["transferable"],
            tailoring_priorities["do_not_add"],
            missing_critical,
            job_type,
        ),
    }

    markdown_report = create_markdown_report(report_data)
    summary_row = create_summary_row(report_data)

    return {
        "report_data": report_data,
        "markdown_report": markdown_report,
        "summary_row": summary_row,
    }


def review_one_job(
    job_file_path,
    resume_text,
    resume_sections,
    resume_bullets,
    normal_keywords,
    critical_keywords,
    resume_normal,
    resume_critical,
    resume_match_details,
    keyword_sections,
    synonyms,
    role_profiles,
):
    """Review one job and save one Markdown report."""
    job_text = read_text_file(job_file_path)
    analysis = analyze_job_text(
        job_file_path.name,
        job_text,
        resume_text,
        resume_sections,
        resume_bullets,
        normal_keywords,
        critical_keywords,
        resume_normal,
        resume_critical,
        resume_match_details,
        keyword_sections,
        synonyms,
        role_profiles,
    )

    output_file_path = create_output_file_path(job_file_path)
    output_file_path.write_text(analysis["markdown_report"], encoding="utf-8")

    summary_row = analysis["summary_row"]
    summary_row["report_file"] = str(output_file_path)
    return summary_row


def write_summary_csv(summary_rows):
    """Save one CSV file that summarizes all job reports."""
    summary_file = OUTPUTS_DIR / "job_summary.csv"
    column_names = [
        "job_file",
        "job_type",
        "fit_category",
        "match_rate",
        "matched_keywords",
        "missing_keywords",
        "recommendation",
        "report_file",
    ]

    try:
        with summary_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=column_names)
            writer.writeheader()
            writer.writerows(summary_rows)
    except PermissionError:
        print(f"Could not update summary CSV: {summary_file}")
        print("Please close the CSV file if it is open, then run the script again.")
        return None

    return summary_file


def main():
    """Run the job helper."""
    OUTPUTS_DIR.mkdir(exist_ok=True)
    JOBS_DIR.mkdir(exist_ok=True)

    if not BASE_RESUME_FILE.exists():
        print("Error: Resume PDF not found.")
        print(f"Please put your resume here: {BASE_RESUME_FILE.resolve()}")
        print("The file name must be exactly: base_resume.pdf")
        return

    resume_text = read_resume_pdf(BASE_RESUME_FILE)
    if resume_text is None:
        return

    if not resume_text:
        print("Warning: No extractable text was found in data/base_resume.pdf.")
        print("This can happen if the PDF is a scan or image-only file.")
        print("Please use a text-based PDF, then run the script again.")
        return

    config = load_analysis_config()
    critical_keywords = config["critical_keywords"]
    normal_keywords = config["normal_keywords"]
    synonyms = config["synonyms"]
    role_profiles = config["role_profiles"]

    resume_context = prepare_resume_context(
        resume_text,
        normal_keywords,
        critical_keywords,
        synonyms,
    )

    job_files = get_job_files()
    if not job_files:
        print("No .txt job files found in data/jobs.")
        print("Add a job description file, then run the script again.")
        return

    summary_rows = []
    for job_file_path in job_files:
        summary_row = review_one_job(
            job_file_path,
            resume_text,
            resume_context["sections"],
            resume_context["bullets"],
            normal_keywords,
            critical_keywords,
            resume_context["resume_normal"],
            resume_context["resume_critical"],
            resume_context["resume_match_details"],
            resume_context["keyword_sections"],
            synonyms,
            role_profiles,
        )
        summary_rows.append(summary_row)
        print(f"Created report: {summary_row['report_file']}")

    summary_file = write_summary_csv(summary_rows)
    if summary_file:
        print(f"Created summary: {summary_file}")

    print("Done!")


if __name__ == "__main__":
    main()
