import pypdf
import re


def _normalize_text(text):
    """Normalize text extracted from the PDF."""
    ligature_map = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
    for ligature, replacement in ligature_map.items():
        text = text.replace(ligature, replacement)

    text = text.replace("\r\n", "\n")
    text = re.sub(r"\s+", " ", text).strip()

    section_headers = [
        "Education",
        "Qualifications",
        "Projects",
        "Experience",
        "Skills",
    ]
    for header in section_headers:
        text = re.sub(rf"({header}\s*:?)", r"\n\1\n", text, flags=re.IGNORECASE)

    return text


def _get_personal_info(pdf_text):
    """Extract personal information from the PDF text."""
    personal = {}
    name_pattern = r"\b[A-Za-z]+(?:\s+[A-Za-z]+)+\b(?=\s+[\w\.-]+@|\s+\|)"
    name_match = re.search(name_pattern, pdf_text, re.MULTILINE)
    personal["name"] = name_match.group().strip() if name_match else ""
    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
    email_match = re.search(email_pattern, pdf_text, re.MULTILINE)
    personal["email"] = email_match.group().strip() if email_match else ""
    phone_pattern = r"\+94[\d\s\-\(\)]{9,12}"
    phone_match = re.search(phone_pattern, pdf_text, re.MULTILINE)
    personal["phone"] = phone_match.group().strip() if phone_match else ""
    return personal


def _get_education(pdf_text):
    """Extract education details from the PDF text."""
    education = []
    education_pattern = r"(?i)\beducation\b\s*:?\s*([\s\S]+?)(?=\n\s*(qualifications|projects|experience|skills|$))"
    education_match = re.search(education_pattern, pdf_text, re.DOTALL)
    if education_match:
        education_text = education_match.group(1).strip()
        education_entries = re.split(r"(?<=\d{4})\s+", education_text)
        degree_pattern = (
            r".*?(?:[Bb]achelor|[Mm]aster|[Dd]octor|University|College|\d{4}).*?"
        )
        for entry in education_entries:
            stripped_entry = entry.strip()
            if stripped_entry and re.match(degree_pattern, stripped_entry):
                education.append(stripped_entry)
    return education


def _get_qualifications(pdf_text):
    """Extract qualifications from the PDF text."""
    qualifications = []
    qualifications_pattern = r"(?i)\bqualifications\b\s*:?\s*([\s\S]+?)(?=\n\s*(projects|experience|skills|$))"
    qualifications_match = re.search(qualifications_pattern, pdf_text, re.DOTALL)
    if qualifications_match:
        qualifications_text = qualifications_match.group(1).strip()
        qual_entries = re.split(
            r"(?<=,\s\d{4})\s+|\s+(?=Certified|Certification)", qualifications_text
        )
        qual_pattern = r".*?(?:[Cc]ertified|[Cc]ertification|\d{4}).*?"
        for entry in qual_entries:
            stripped_entry = entry.strip()
            if stripped_entry and re.match(qual_pattern, stripped_entry):
                qualifications.append(stripped_entry)
    return qualifications


def _get_projects(pdf_text):
    """Extract projects from the PDF text."""
    projects = []
    projects_pattern = r"(?i)\bprojects\b\s*:?\s*([\s\S]+)$"
    projects_match = re.search(projects_pattern, pdf_text, re.DOTALL)
    if not projects_match:
        projects_pattern = (
            r"(?i)\bprojects\b\s*:?\s*([\s\S]+?)(?=\n\s*(experience|skills))"
        )
        projects_match = re.search(projects_pattern, pdf_text, re.DOTALL)

    if projects_match:
        projects_text = projects_match.group(1).strip()
        project_entries = re.split(r"(?<=\.)\s+", projects_text)
        project_pattern = r".+\S.+"
        for entry in project_entries:
            stripped_entry = entry.strip()
            if stripped_entry and re.match(project_pattern, stripped_entry):
                projects.append(stripped_entry)
    return projects


def parse_cv_pdf(pdf_text, file_path):
    """Parse CV data from PDF text.

    Args:
        pdf_text (str): The raw text extracted from the PDF.
        file_path (str): The path or identifier of the PDF (e.g., S3 key).

    Returns:
        dict: Parsed CV data including personal info, education, qualifications, projects, and link.
    """
    normalized_text = _normalize_text(pdf_text)
    return {
        "personal_info": _get_personal_info(normalized_text),
        "education": _get_education(normalized_text),
        "qualifications": _get_qualifications(normalized_text),
        "projects": _get_projects(normalized_text),
        "cv_public_link": file_path,
    }


# CVParser class for local use
class CVParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.pdf_text = self._read_pdf()

    def _read_pdf(self):
        if not self.file_path.lower().endswith(".pdf"):
            raise ValueError("File must be in .pdf format.")
        with open(self.file_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            if len(reader.pages) > 1:
                raise ValueError("PDF must be a single page only")
            text = reader.pages[0].extract_text() or ""
        return text

    def get_cv_data(self):
        return parse_cv_pdf(self.pdf_text, self.file_path)
