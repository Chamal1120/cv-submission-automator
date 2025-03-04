import pypdf


def extract_text(file_path):
    with open(file_path, "rb") as file:
        reader = pypdf.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


if __name__ == "__main__":
    PDF_PATH = "Test-cv.pdf"
    pdf_text = extract_text(PDF_PATH)
    print("Raw PDF text:")
    print(pdf_text)
