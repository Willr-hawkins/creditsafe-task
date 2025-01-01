from django.shortcuts import render
from .forms import FileUploadForm
from django.conf import settings
import os
from django.http import JsonResponse, HttpResponse
import json

# Imports for pytesseract, pdf2image, spaCy and langdetect
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import spacy
from langdetect import detect

def upload_file(request):
    # handle file form submissions for scanning.

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = form.save()
            # Process uploaded files
            file_path = os.path.join(settings.MEDIA_ROOT, upload_file.file.name)
            extracted_text = process_file(file_path)
            # Intergrate NLP
            data = process_text(extracted_text)

            # Prepare JSON reponse
            response_data = {
                'Company Name': data.get('Company Name', ''),
                'Company Indentifier': data.get('Company Identifier', ''),
                'Doument Purpose': data.get('Document Purpose', ''),
                'Key Terms': data.get('Key Terms', []),
            }

            # Create a downloadable JSON file
            response_json = json.dumps(response_data, indent=4)
            response = HttpResponse(response_json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="extracted_info.json"'
            return response
    else:
        form = FileUploadForm()
    
    context = {
        'form': form,
    }

    return render(request, 'extractor/upload.html', context)

def process_file(file_path):
    # Process uploaded files using pytesseract

    # Check if the file is a pdf or image
    if file_path.endswith('.pdf'):
        # Convert pdf to image
        images = convert_from_path(file_path)
        image = images[0]
    else:
        # Open the file with PIL
        image = Image.open(file_path)
    # Perform OCR
    text = pytesseract.image_to_string(image)
    return text

def process_text(text):
    # Using spaCy and langdetect, verify the language used and extract the key entities.

    language = detect(text)
    nlp = spacy.load(f"{language}_core_news_sm")
    doc = nlp(text)

    # Initialize reulsts
    data = {
        'Company Name': '',
        'Company Indentifier': '',
        'Document Purpose': '',
        'key Terms': [],
    }

    # Extract entities 
    for ent in doc.ents:
        if ent.label_ == 'ORG':
            data['Company Name'] = ent.text
        elif ent.label_ == 'MONEY':
            data['Company Indentifier'] = ent.text

    return data