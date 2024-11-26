import requests

def test_process_pdf():
    # Replace with your PDF path
    pdf_path = r"C:\Users\Thanh\Documents\Parser\World_History_Volume_1-WEB.pdf"
    
    # Test /process_pdf endpoint
    with open(pdf_path, 'rb') as pdf_file:
        files = {'file': pdf_file}
        response = requests.post('http://localhost:8000/process_pdf', files=files)
    
    print("\n=== Process PDF Response ===")
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(response.json())
    
    # Save the PDF hash for the next test
    pdf_hash = response.json()['pdf_hash']
    return pdf_hash

def test_generate_questions(chapter_number=1):
    # Replace with your PDF path
    pdf_path = r"C:\Users\Thanh\Documents\Parser\World_History_Volume_1-WEB.pdf"
    
    # Test /generate_chapter_questions endpoint
    with open(pdf_path, 'rb') as pdf_file:
        files = {'file': pdf_file}
        response = requests.post(
            f'http://localhost:8000/generate_chapter_questions',
            files=files,
            params={'chapter': chapter_number}
        )
    
    print("\n=== Generate Questions Response ===")
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(response.json())

if __name__ == "__main__":
    # Test process_pdf endpoint
    pdf_hash = test_process_pdf()
    
    # Test generate_questions endpoint for chapter 1
    test_generate_questions(1) 