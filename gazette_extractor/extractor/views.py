import os
import json
import re
from datetime import datetime
from django.shortcuts import render
from .forms import FileUploadForm
from django.conf import settings
from django.http import JsonResponse, HttpResponse

# Imports for pytesseract, pdf2image, spaCy and langdetect
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import spacy
from langdetect import detect
from googletrans import Translator
from unicodedata import normalize

def upload_file(request):
    """ Handle file form submissions for scanning """

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = form.save()
            file_path = os.path.join(settings.MEDIA_ROOT, upload_file.file.name)
            extracted_text = process_file(file_path)
            document_date = extract_document_date(extracted_text)
            # Text processing to extract key details
            data = process_text(extracted_text, document_date)
            # Return JSON response
            response_json = json.dumps(data, indent=4, ensure_ascii=False)
            response = HttpResponse(response_json, content_type='application/json; charset=utf8')
            response['Content-Disposition'] = 'attachment; filename="extracted_info.json"'
            return response
    else:
        form = FileUploadForm()
    return render(request, 'extractor/upload.html', {'form': form})

def extract_document_date(text):
    """ Extract a date from the document text if present """
    date_match = re.search(r'(?:le|date)\s*[:\-]?\s*(\d{1,2} [a-zA-Z]+ \d{4})', text)
    if date_match:
        return datetime.strptime(date_match.group(1), '%d %B %Y').date()
    return None

def process_file(file_path):
    """ Process the uploaded file using pytesseract """

    # Check if the file is a PDF or image
    if file_path.endswith('.pdf'):
        images = convert_from_path(file_path)
        image = images[0]
    else:
        image = Image.open(file_path)
    
    text = pytesseract.image_to_string(image)
    print(f"OCR Text: {text}")
    text = normalize('NFKC', text)  # Normalize Unicode special characters
    return text

def process_text(text, document_date):
    """ Process text extracted from the file """

    # Clean up OCR text by fixing unwanted line breaks and extra spaces
    text = fix_ocr_text(text)

    # Detect language (if needed for translations or other logic)
    language = detect(text)

    # Load the appropriate spaCy NLP model (e.g., French or English)
    try:
        nlp = spacy.load(f"{language}_core_news_sm")
    except OSError:
        nlp = spacy.load("en_core_web_sm")  # Fallback to English if language model is not found
    
    doc = nlp(text)

    data = {
        'Company Name': '',
        'Company Identifier': '',
        'Document Purpose': '',
        'Additional Information': {},
    }

    # Extract Company Name using NLP entity recognition (ORG)
    for ent in doc.ents:
        if ent.label_ == 'ORG':
            data['Company Name'] = normalize('NFKC', ent.text).strip()

    # Extract Company Identifier using regex (e.g., Tax ID, Company Number)
    identifier_match = re.search(r'N° d\'entreprise :\s*(\d{4} \d{3} \d{3})', text)
    if identifier_match:
        data['Company Identifier'] = normalize('NFKC', identifier_match.group(1))

    # Extract document purpose using the refined regex
    document_purpose = extract_document_purpose(text)
    data['Document Purpose'] = document_purpose

    # Extract director appointment info using refined logic
    director_info = extract_director_appointment_info(text, document_date)
    if director_info:
        data['Additional Information'] = director_info

    return data

def fix_ocr_text(text):
    """ Clean up the OCR text by removing line breaks and extra spaces """
    text = re.sub(r'(?<=\w)-\n(?=\w)', '', text)
    text = text.replace("\n", " ")
    text = text.replace("  ", " ")
    
    return text

def extract_document_purpose(text):
    """ Extract the document purpose from the text """

    purpose_keywords = [
        r'(?:Objet de Pacte|Objet de la résolution|Object)\s*[:\-]?\s*(.*?)(?:Extrait de|N° d\'entreprise|Résumé)',
        r'(?:Pour le but de|résolution\s*[:\-]?\s*(.*))',
        r'(?:Acte)\s*[:\-]?\s*(.*)',
    ]

    for pattern in purpose_keywords:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Purpose not found"

def extract_director_appointment_info(text, document_date):
    """ Extract director appointment information from the text """

    director_info = {
        'Director Name': '',
        'Position': '',
        'Effective Date': '',
    }

    # Refined regex for Director Name
    director_name_match = re.search(r'(M\.\s*[A-Za-zÀ-ÿ\s]+)\s*(?:nommé|désigné)', text, re.IGNORECASE)
    if director_name_match:
        director_info['Director Name'] = director_name_match.group(1).strip()

    # Refined regex for Director Position
    position_match = re.search(r'(administrateur|directeur|gérant|CEO|CFO)', text, re.IGNORECASE)
    if position_match:
        director_info['Position'] = position_match.group(1).strip()

    # Refined regex for Effective Date
    date_match = re.search(r'effectif\s*le\s*(\d{1,2}\s*[a-zA-Z]+\s*\d{4})', text, re.IGNORECASE)
    if date_match:
        effective_date_str = date_match.group(1)
        try:
            effective_date = datetime.strptime(effective_date_str, '%d %B %Y').date()
            director_info['Effective Date'] = effective_date.strftime('%Y-%m-%d')
        except ValueError:
            director_info['Effective Date'] = 'Invalid Date'
    elif document_date:
        director_info['Effective Date'] = document_date.strftime('%Y-%m-%d')

    return director_info

def translate_text_to_english(text, src_language):
    """ Translate text to English using Google Translate API """
    translator = Translator()
    translated = translator.translate(text, src=src_language, dest='en')
    return translated.text