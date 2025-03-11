from models.cv_parser import CVParser
import json


def main():
    """Run the CVParser locally to extract data from a PDF."""

    pdf_path = "Test-cv.pdf"  # Test pdf

    try:
        parser = CVParser(pdf_path)
        cv_data = parser.get_cv_data()

        print("Extracted CV Data:")
        print(json.dumps(cv_data, indent=2))

    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
