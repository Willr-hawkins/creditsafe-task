from django.shortcuts import render
from .forms import FileUploadForm

def upload_file(request):
    # handle file form submissions for scanning.

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, 'extractor/success.html')
    else:
        form = FileUploadForm()
    
    context = {
        'form': form,
    }

    return render(request, 'extractor/upload.html', context)

