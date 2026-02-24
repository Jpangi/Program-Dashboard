from django import forms
from .models import Program, CSVupload


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'program_code', 'description', 'start_date', 'end_date']



class CSVUploadForm(forms.ModelForm):
    class Meta:
        model = CSVupload
        fields = ['program', 'file']