from django import forms
from .models import UploadedFile

class FileUploadForm(forms.ModelForm):
    # Form for user to upload a gazette file for scanning

    class Meta:
        model = UploadedFile
        fields = ['file']