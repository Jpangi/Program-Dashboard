from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import ProgramForm, CSVUploadForm
from .models import Program, CSVupload
from .utils.csv_processor import EVMCSVProcessor


def home(request):
    programs = Program.objects.all()
    return render(request, 'home.html', {'programs': programs})

def create_program(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProgramForm()
    
    return render(request, 'create_program.html', {'form': form})

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload_record = form.save(commit=False)
            upload_record.uploaded_by = request.user
            upload_record.status = 'pending'
            upload_record.original_file = request.FILES['file'].name
            upload_record.save()

            request.FILES['file'].seek(0) 

            processor = EVMCSVProcessor(
                csv_file=request.FILES['file'],
                upload_record=upload_record,
                program=upload_record.program
            )
            processor.process()

            return redirect('home')
    else:
        form = CSVUploadForm()

    return render(request, 'upload_csv.html', {'form': form})


def program_detail(request, pk):
    program = Program.objects.get(pk=pk)
    return render(request, 'program_detail.html', {'program': program})