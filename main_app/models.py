from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, Avg, Max, Min
from django.utils import timezone
from decimal import Decimal


# 1. `Program` - Top-level program
class Program(models.Model):
    name = models.CharField(max_length=50)
    program_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
     # Period of Performance
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"{self.name} - {self.program_code}"
    #Calculated fields

    @property # allows you to call a function withtout putting function() call at the bottom
    def latest_bcws(self):
        """ Latest Budget Value"""
        #first need to get the latest date
        #orders by date decending, gets the values of the ordered list by date, flattens it to be [feb, march] as example.
        #grabs the first date so latest_date = feb 
        latest_date = self.evm_data.filter(cobra_set='BCWS',results='Dollars').order_by('-date').values_list('date', flat=True).first()
        if not latest_date:
            return 0
        
        total = self.evm_data.filter(cobra_set='BCWS',results='Dollars', date=latest_date).aggregate(total=Sum('value'))['total']
        return total or 0
    
    #recent Indicators
    @property # allows you to call a function withtout putting function() call at the bottom
    def latest_bcwp(self):
        """ Latest performance Value"""
        #first need to get the latest date
        latest_date = self.evm_data.filter(cobra_set='BCWP',results='Dollars').order_by('-date').values_list('date', flat=True).first()
        if not latest_date:
            return 0
        
        total = self.evm_data.filter(cobra_set='BCWP',results='Dollars', date=latest_date).aggregate(total=Sum('value'))['total']
        return total or 0
    @property # allows you to call a function withtout putting function() call at the bottom
    def latest_acwp(self):
        """ Latest Actuals Value"""
        #first need to get the latest date
        latest_date = self.evm_data.filter(cobra_set='ACWP',results='Dollars').order_by('-date').values_list('date', flat=True).first()
        if not latest_date:
            return 0
        
        total = self.evm_data.filter(cobra_set='ACWP',results='Dollars', date=latest_date).aggregate(total=Sum('value'))['total']
        return total or 0
    


    """Cumulative Data"""
    @property # allows you to call a function withtout putting function() call at the bottom
    def cumulative_bcws(self):
        """ Cumulative Budget Value"""
        
        total = self.evm_data.filter(cobra_set='BCWS',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
    
    #recent Indicators
    @property # allows you to call a function withtout putting function() call at the bottom
    def cumulative_bcwp(self):
        """ Cumulative performance Value"""
        total = self.evm_data.filter(cobra_set='BCWP',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
    @property # allows you to call a function withtout putting function() call at the bottom
    def cumulative_acwp(self):
        """ Cumulative Actuals Value"""
        total = self.evm_data.filter(cobra_set='ACWP',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
    
    #Performance indicators
    @property # allows you to call a function withtout putting function() call at the bottom
    def monthly_cpi(self):
        """CPI for Control Account"""
        acwp = self.latest_acwp
        bcwp = self.latest_bcwp
        if acwp == 0:
            return 0
        return bcwp / acwp
    @property # allows you to call a function withtout putting function() call at the bottom
    def monthly_spi(self):
        """SPI for Control Account"""
        bcws = self.latest_bcws
        bcwp = self.latest_bcwp
        if bcws == 0:
            return 0
        return bcwp / bcws
    

    @property # allows you to call a function withtout putting function() callat the bottom
    def cumulative_cpi(self):
        """CPI for Control Account"""
        acwp = self.cumulative_acwp
        bcwp = self.cumulative_bcwp
        if acwp == 0:
            return 0
        return bcwp / acwp
    @property # allows you to call a function withtout putting function() callat the bottom
    def cumulative_spi(self):
        """SPI for Control Account"""
        bcws = self.cumulative_bcws
        bcwp = self.cumulative_bcwp
        if bcws == 0:
            return 0
        return bcwp / bcws
    # Cumulative Indicators
    @property # allows you to call a function withtout putting function() callat the bottom
    def eac(self):
        """Total EAC for the Control Account"""
        total = self.evm_data.filter(cobra_set='EAC',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
    @property # allows you to call a function withtout putting function() callat the bottom
    def bac(self):
        """Total BAC for the Control Account"""
        total = self.evm_data.filter(cobra_set='BCWS',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
# 2. `ControlAccount` - Control accounts under programs
class ControlAccount(models.Model):
    ca_name = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='control_accounts' #allows for reverse relationship Program <-> CA models
    )
    def __str__(self):
        return f"{self.ca_name} - {self.program.name}"
# 3. `WorkPackage` - Work packages under control accounts
class WorkPackage(models.Model):
    wp_name = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    control_account = models.ForeignKey(
        ControlAccount, 
        on_delete=models.CASCADE, 
        related_name='work_packages' #allows for reverse relationship CA <->WP models
    )
    def __str__(self):
        return f"{self.wp_name} - {self.control_account.ca_name}"
# 4. `EVMData` - Individual data points from CSV
    #every column in the CSV file with the data
class EVMData(models.Model):
    control_account = models.ForeignKey(
        ControlAccount,
        on_delete=models.CASCADE,
        related_name='evm_data', #allows for reverse relationship CA <->Data models
        null=True,
        blank=True
    )
    work_package = models.ForeignKey(
        WorkPackage,
        on_delete=models.CASCADE,
        related_name='evm_data',#allows for reverse relationship WP <->Data models
        null=True,
        blank=True
    )
    # resource column from csv
    resource = models.CharField(max_length=200, blank=True)
    #Element of Cost column from csv
    eoc_options = [
        ('Labor', 'Labor'),
        ('Material', 'Material'),
        ('ODC', 'ODC'),
        ('PCL', 'PCL'),
    ]
    eoc = models.CharField(max_length=50, choices=eoc_options)
    # results column from csv
    result_options = [
        ('Dollars', 'Dollars'),
        ('FTE', 'FTE'),
        ('Hours', 'Hours'),
        ('Direct', 'Direct'),
    ]
    results = models.CharField(max_length=50, choices=result_options)
    #ipt column

    #cam column
    cam = models.CharField(max_length=50)
    #set name column
    set_options = [
        ('EAC', 'EAC (Estimate at Completion)'),
        ('CEAC', 'CEAC (Cumulative EAC)'),
        ('BCWP', 'BCWP (Earned Value)'),
        ('BCWS', 'BCWS (Planned Value)'),
        ('ACWP', 'ACWP (Actual Cost)'),
        ('BAC', 'BAC (Budget at Completion)'),
    ]
    cobra_set = models.CharField(max_length=100, choices=set_options)
    #date column
    date = models.DateField()
   
    #value column
    value = models.DecimalField(max_digits=15, decimal_places=2)

    # create indexes for faster querys
    class Meta:
        indexes = [
            models.Index(fields=['program', 'date']),
            models.Index(fields=['control_account','cobra_set', 'date']),
            models.Index(fields=['cobra_set', 'date']),
        ]
    def __str__(self):
        return f"{self.control_account.ca_name} - {self.cobra_set} - {self.date}"
    
    

# 5. `CSVUpload` - Track file uploads
# 6. `EVMSnapshot` - Monthly aggregated data
# 7. `Alert` - System alerts 
