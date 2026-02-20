from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, Avg, Max, Min
from django.utils import timezone
from decimal import Decimal

#See doc file for high level summary of each model

# ============================================================
# 1. `Program` - Top-level program
# ============================================================
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


    """Monthly Values"""
    @property
    # allows calling like:
    # program.latest_bcws
    # instead of:
    # program.latest_bcws()

    def latest_bcws(self):

        latest_date = self.evm_data.filter(
            cobra_set='BCWS',
            results='Dollars'
        ).order_by('-date').values_list('date', flat=True).first()

        # BREAKDOWN:

        # self.evm_data
        # reverse relationship from ControlAccount
        # because ControlAccount has:
        # related_name='evm_data'

        # filter()
        # filters database rows

        # cobra_set='BCWS'
        # selects Planned Value rows

        # order_by('-date')
        # sorts newest first

        # values_list('date', flat=True)
        # returns ONLY the date column

        # first()
        # gets newest date

        if not latest_date:
            return 0
        # prevents crash if no data exists

        total = self.evm_data.filter(
            cobra_set='BCWS',
            results='Dollars',
            date=latest_date
        ).aggregate(total=Sum('value'))['total']

        # aggregate()
        # runs SQL:
        # SELECT SUM(value)

        return total or 0
        # prevents returning None
    
    #recent Indicators
    @property 
    def latest_bcwp(self):
        """ Latest performance Value"""
        #first need to get the latest date
        latest_date = self.evm_data.filter(cobra_set='BCWP',results='Dollars').order_by('-date').values_list('date', flat=True).first()
        if not latest_date:
            return 0
        
        total = self.evm_data.filter(cobra_set='BCWP',results='Dollars', date=latest_date).aggregate(total=Sum('value'))['total']
        return total or 0
    @property 
    def latest_acwp(self):
        """ Latest Actuals Value"""
        #first need to get the latest date
        latest_date = self.evm_data.filter(cobra_set='ACWP',results='Dollars').order_by('-date').values_list('date', flat=True).first()
        if not latest_date:
            return 0
        
        total = self.evm_data.filter(cobra_set='ACWP',results='Dollars', date=latest_date).aggregate(total=Sum('value'))['total']
        return total or 0
    


    """Cumulative Data"""
    @property 
    def cumulative_bcws(self):
        #cumulative bcws
        
        total = self.evm_data.filter(cobra_set='BCWS',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
        # Works the same as latest function
        # but without filtering by date
        # sums ALL historical values

    @property 
    def cumulative_bcwp(self):
        #cumulative bcwp
        total = self.evm_data.filter(cobra_set='BCWP',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
    @property 
    def cumulative_acwp(self):
        #cumulative Actuals
        total = self.evm_data.filter(cobra_set='ACWP',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
    
    """Performance Data"""
    @property 
    def monthly_cpi(self):
        # monthly CPI for Control Account
        acwp = self.latest_acwp
        bcwp = self.latest_bcwp
        if acwp == 0:
            return 0
        return bcwp / acwp
    @property 
    def monthly_spi(self):
        # monthly SPI for Control Account
        bcws = self.latest_bcws
        bcwp = self.latest_bcwp
        if bcws == 0:
            return 0
        return bcwp / bcws
    

    @property 
    def cumulative_cpi(self):
        # Cumulative CPI for Control Account
        acwp = self.cumulative_acwp
        bcwp = self.cumulative_bcwp
        if acwp == 0:
            return 0
        return bcwp / acwp
    @property 
    def cumulative_spi(self):
        # Cumulative CPI for Control Account
        bcws = self.cumulative_bcws
        bcwp = self.cumulative_bcwp
        if bcws == 0:
            return 0
        return bcwp / bcws

    @property 
    def eac(self):
        # EAC for Control Account
        total = self.evm_data.filter(cobra_set='EAC',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
    @property 
    def bac(self):
        # BAC for Control Account
        total = self.evm_data.filter(cobra_set='BCWS',results='Dollars').aggregate(total=Sum('value'))['total']
        return total or 0
    
# ============================================================
# 2. `ControlAccount` - Control accounts under programs
# ============================================================
class ControlAccount(models.Model):
    ca_name = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    program = models.ForeignKey(
        Program,
        # creates relationship to Program

        on_delete=models.CASCADE,
        # if Program deleted
        # delete ControlAccount

        related_name='control_accounts' 
        # allows reverse access: Program <-> CA 
        # program.control_accounts.all()
    )
    def __str__(self):
        return f"{self.ca_name} - {self.program.name}"

# ============================================================
# 3. `WorkPackage` - Work packages under control accounts
# ============================================================
class WorkPackage(models.Model):
    wp_name = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    control_account = models.ForeignKey(
        ControlAccount, 
        on_delete=models.CASCADE, 
        related_name='work_packages' 
        # allows reverse access: CA <->WP
        # program.control_accounts.all()
    )
    def __str__(self):
        return f"{self.wp_name} - {self.control_account.ca_name}"

# ============================================================
# 4. `EVMData` - Individual data points from CSV
# ============================================================
    #every column in the CSV file with the data
class EVMData(models.Model):
    control_account = models.ForeignKey(
        ControlAccount,
        on_delete=models.CASCADE,
        related_name='evm_data', 
        # allows: control_account.evm_data.all() - CA <->Data
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
    # choices does 2 things:  restricts allowed values and creates dropdown in admin

    # results column from csv
    result_options = [
        ('Dollars', 'Dollars'),
        ('FTE', 'FTE'),
        ('Hours', 'Hours'),
        ('Direct', 'Direct'),
    ]
    results = models.CharField(max_length=50, choices=result_options)
    #ipt column


    cam = models.IntegerField()

    set_options = [
        ('EAC', 'EAC (Estimate at Completion)'),
        ('CEAC', 'CEAC (Cumulative EAC)'),
        ('BCWP', 'BCWP (Earned Value)'),
        ('BCWS', 'BCWS (Planned Value)'),
        ('ACWP', 'ACWP (Actual Cost)'),
        ('BAC', 'BAC (Budget at Completion)'),
    ]
    cobra_set = models.CharField(max_length=100, choices=set_options)
 
    date = models.DateField()
    #stores reporting month
   

    value = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.control_account.ca_name} - {self.cobra_set} - {self.date}"
    
# ============================================================
# 5. `EVMSnapshot` - Monthly aggregated data
# ============================================================
class EVMSnapshot(models.Model):
    """
    Historical Point in time data for trends
    generates when csv is uploaded
    """

    program = models.ForeignKey(
        Program, 
        on_delete=models.CASCADE,
        related_name='snapshots'
        )
    control_account = models.ForeignKey(
        ControlAccount,
        on_delete=models.CASCADE,
        related_name='snapshots'
    )
    snapshot_date = models.DateField()  # End of month 

    # stores aggregated values
    bcws_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bcwp_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    acwp_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    eac_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    #stores calculated values
    cpi = models.DecimalField(max_digits=5, decimal_places=3, default=0)
    spi = models.DecimalField(max_digits=5, decimal_places=3, default=0)
    cv = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sv = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        ca_name = self.control_account.ca_name if self.control_account else "Program-wide"
        return f"{self.program.program_code} - {ca_name} - {self.snapshot_date}"

# ============================================================
# 6. `CSVupload` - Stores data about the upload
# ============================================================
class CSVupload(models.Model):
    STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ]
    #defines the allowed values
    #first value ex: pending gets stored in database, second value Pending shown to UI
    #prevents invalid values like random_status
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='csv_upload'
    )

    #stores the person who uploaded the file
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, # if the user is deleted keep the file
        null=True
    )

  
    file = models.FileField(upload_to='uploads/%Y/%m/')
    #where the file actually gets uploaded and changes name of file
    # stores file in: media/uploads/2026/02/


    original_file = models.CharField(max_length=255)
    #original File name

    
    uploaded_at = models.DateField(auto_now_add=True)
    # auto sets date when created
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)