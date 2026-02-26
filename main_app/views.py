from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import ProgramForm, CSVUploadForm
from .models import Program, CSVupload
from .utils.csv_processor import EVMCSVProcessor
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.urls import reverse_lazy
import json
from django.views.generic.edit import CreateView, UpdateView, DeleteView

@login_required 
def programs(request):
    programs = Program.objects.filter(owner=request.user) 
    return render(request, 'programs.html', {'programs': programs})
@login_required 
def create_program(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save(commit=False)
            program.owner = request.user   # attach the logged-in user
            form.save()
            return redirect('programs')
    else:
        form = ProgramForm()
    
    return render(request, 'create_program.html', {'form': form})
@login_required 
def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES, user=request.user)
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

            return redirect('programs')
    else:
        form = CSVUploadForm(user=request.user)

    return render(request, 'upload_csv.html', {'form': form})




@login_required 
def program_detail(request, pk):
    program = Program.objects.get(pk=pk)
    
    cobra_sets = ['BCWS', 'BCWP', 'ACWP']
    results_types = ['FTE', 'Dollars', 'Direct']
    
    chart_data = {}
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']

    for cobra_set in cobra_sets:
        chart_data[cobra_set] = {}
        for results in results_types:
            fte_data = program.evm_data.filter(
                cobra_set=cobra_set,
                results=results
            ).values('date', 'ipt').annotate(total=Sum('value')).order_by('date')

            dates = sorted(set(str(item['date']) for item in fte_data))
            ipts = sorted(set(item['ipt'] for item in fte_data))
            lookup = {(str(item['date']), item['ipt']): float(item['total']) for item in fte_data}

            datasets = []
            for i, ipt in enumerate(ipts):
                datasets.append({
                    'label': ipt,
                    'data': [lookup.get((date, ipt), 0) for date in dates],
                    'backgroundColor': colors[i % len(colors)],
                })

            chart_data[cobra_set][results] = {'dates': dates, 'datasets': datasets}

    return render(request, 'program_detail.html', {
        'program': program,
        'chart_data': json.dumps(chart_data),
    })

def signup(request):
    error_message = ''
    if request.method == 'POST':
        # This is how to create a 'user' form object
        # that includes the data from the browser
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # This will add the user to the database
            user = form.save()
            # This is how we log a user in
            login(request, user)
            return redirect('programs')
        else:
            error_message = 'Invalid sign up - try again'
    # A bad POST or a GET request, so render signup.html with an empty form
    form = UserCreationForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'signup.html', context)

class Home(LoginView):
    template_name = 'home.html'

class ProgramUpdate(LoginRequiredMixin, UpdateView):
    model = Program
    fields = ['name', 'end_date', 'description']
    success_url = reverse_lazy('programs')

    def get_queryset(self):
        return Program.objects.filter(owner=self.request.user)

class ProgramDelete(LoginRequiredMixin, DeleteView):
    model = Program
    success_url = '/programs/'

    def get_queryset(self):
        return Program.objects.filter(owner=self.request.user) 