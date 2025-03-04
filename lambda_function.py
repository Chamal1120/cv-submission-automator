import re
import pypdf


# Extract all text in the pdf
def extract_text(file_path):
    with open(file_path, "rb") as file:
        reader = pypdf.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


# Extract personal info from all text
def extract_personal_info(pdf_text):
    personal_info = {}

    # Extract Name: Two or more words with letters
    name_pattern = r"^[A-Za-z]+(?:\s+[A-Za-a]+)+"
    name_match = re.search(name_pattern, pdf_text, re.MULTILINE)
    personal_info["name"] = name_match.group() if name_match else ""

    # Extract Email: Standard Email format
    email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
    email_match = re.search(email_pattern, pdf_text, re.MULTILINE)
    personal_info["email"] = email_match.group() if email_match else ""

    # Extract phone no: Standard Sri Lankan format
    phone_pattern = r"\+94[\d\s\-\(\)]{9,12}"
    phone_match = re.search(phone_pattern, pdf_text, re.MULTILINE)
    personal_info["phone"] = phone_match.group() if phone_match else ""

    return personal_info


if __name__ == "__main__":
    PDF_PATH = "Test-cv.pdf"
    extracted_text = extract_text(PDF_PATH)
    print("Raw PDF text:")
    print(extracted_text)
    personal_info = extract_personal_info(extracted_text)
    print("Personal info:")
    print(personal_info)
