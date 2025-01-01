from django.db import models

class UploadedFile(models.Model):
    # Upload a file for scanning
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
