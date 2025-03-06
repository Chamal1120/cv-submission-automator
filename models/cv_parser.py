import pypdf
import re


class CVParser:
    """Parse CV data from a single-page PDF file.

    This class processes a PDF file, extracts structured data such as personal information,
    education, qualifications, and projects, and provides it through a single public method.
    All internal methods are private to enforce encapsulation.

    Attributes:
        file_path (str): The path to the PDF file to be processed.
        pdf_text (str): The normalized text extracted from the PDF.
    """

    def __init__(self, file_path):
        """Initialize the CVParser with a file path and process the PDF.

        Args:
            file_path (str): The path to the PDF file to parse.

        Raises:
            ValueError: If the file is not a PDF or has more than one page.
        """

        self.file_path = file_path
        self.pdf_text = self._read_pdf()

    # Read the full pdf
    def _read_pdf(self):
        """Read and normalize text from the PDF file.

        This method handles file validation, text extraction, and normalization steps like
        ligature replacement and section header formatting.

        Returns:
            str: The normalized text extracted from the PDF.

        Raises:
            ValueError: If the file format is invalid or the PDF has multiple pages.
        """

        if not self.file_path.lower().endswith("pdf"):
            raise ValueError("File must be in .pdf format.")

        # Open the pdf
        with open(self.file_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            text = ""

            # Check page count
            if len(reader.pages) > 1:
                raise ValueError("PDF must be a single page only.")
            text += reader.pages[0].extract_text() or ""

        # Define a ligature_map
        ligature_map = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}

        # Replace ligatures with normal letters
        for ligature, replacement in ligature_map.items():
            text = text.replace(ligature, replacement)

        text = text.replace("\r\n", "\n")
        text = re.sub(r"\s+", " ", text).strip()

        # Helper list: Define section headers
        section_headers = [
            "Education",
            "Qualifications",
            "Projects",
            "Experience",
            "Skills",
        ]

        # Search the extracted text and add new lines before and after
        for header in section_headers:
            text = re.sub(rf"({header}\s*:?)", r"\n\1\n", text, flags=re.IGNORECASE)

        return text

    def _get_personal_info(self):
        """Extract personal information from the PDF text.

        Returns:
            dict: A dictionary containing name, email, and phone number extracted from the text.
        """

        # Dict to store the personal info
        personal = {}

        # Search and add the name, email and phone to personal
        name_pattern = r"\b[A-Za-z]+(?:\s+[A-Za-z]+)+\b(?=\s+[\w\.-]+@|\s+\|)"
        name_match = re.search(name_pattern, self.pdf_text, re.MULTILINE)
        personal["name"] = name_match.group().strip() if name_match else ""
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        email_match = re.search(email_pattern, self.pdf_text, re.MULTILINE)
        personal["email"] = email_match.group().strip() if email_match else ""
        phone_pattern = r"\+94[\d\s\-\(\)]{9,12}"
        phone_match = re.search(phone_pattern, self.pdf_text, re.MULTILINE)
        personal["phone"] = phone_match.group().strip() if phone_match else ""

        return personal

    def _get_education(self):
        """Extract education details from the PDF text.

        Returns:
            list: A list of education entries (e.g., degrees, institutions, years).
        """

        # list to store education
        education = []

        # Capture from Education header upto next section or end of the text
        education_pattern = r"(?i)\beducation\b\s*:?\s*([\s\S]+?)(?=\n\s*(qualifications|projects|experience|skills|$))"
        education_match = re.search(education_pattern, self.pdf_text, re.DOTALL)
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

    def _get_qualifications(self):
        """Extract qualifications from the PDF text.

        Returns:
            list: A list containing qualification entries (eg: certifications, years).
        """

        # list to store qualifications
        qualifications = []

        # Capture from qualifications header upto next section or end of the text
        qualifications_pattern = r"(?i)\bqualifications\b\s*:?\s*([\s\S]+?)(?=\n\s*(projects|experience|skills|$))"

        qualifications_match = re.search(
            qualifications_pattern, self.pdf_text, re.DOTALL
        )

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

    def _get_projects(self):
        """Extract projects from the PDF text.

        Returns:
            list: A list of project descriptions.
        """

        # list to store the projects
        projects = []

        # Capture from qualifications header upto next section or end of the text
        projects_pattern = r"(?i)\bprojects\b\s*:?\s*([\s\S]+)$"  # Match to end
        projects_match = re.search(projects_pattern, self.pdf_text, re.DOTALL)
        if not projects_match:  # Fallback if sections follow
            projects_pattern = (
                r"(?i)\bprojects\b\s*:?\s*([\s\S]+?)(?=\n\s*(experience|skills))"
            )
            projects_match = re.search(projects_pattern, self.pdf_text, re.DOTALL)

        if projects_match:
            projects_text = projects_match.group(1).strip()
            print("Projects Text:", repr(projects_text))  # Debug
            project_entries = re.split(r"(?<=\.)\s+", projects_text)
            project_pattern = r".+\S.+"
            for entry in project_entries:
                stripped_entry = entry.strip()
                if stripped_entry and re.match(project_pattern, stripped_entry):
                    projects.append(stripped_entry)
        else:
            print("No Projects section found.")  # Debug
        return projects

    def get_cv_data(self):
        """Extract all CV data from the PDF file.

        This is the primary public method to access the parsed CV data, combining all
        internal extraction methods into a single structured output.

        Returns:
            dict: A dictionary containing personal_info, education, qualifications,
                  projects, and a cv_public_link.
        """

        return {
            "personal_info": self._get_personal_info(),
            "education": self._get_education(),
            "qualifications": self._get_qualifications(),
            "projects": self._get_projects(),
            "cv_public_link": f"file://{self.file_path}",
        }
