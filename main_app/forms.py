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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # pull user out before super().__init__
        super().__init__(*args, **kwargs)
        if user:
            self.fields['program'].queryset = Program.objects.filter(owner=user)