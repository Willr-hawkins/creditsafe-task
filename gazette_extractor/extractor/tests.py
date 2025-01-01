from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UploadedFile

class FileUploadedTest(TestCase):
    """ Test is files are uploaded succesfully and 
    that is invalid files are uploaded the proper error response is returned. """

    def test_file_upload(self):
