import csv
import io
from decimal import Decimal
from datetime import datetime
from django.db import transaction


from main_app.models import Program, ControlAccount, WorkPackage, EVMData

# Import your Django models so we can create database records


# ============================================================================
# CLASS DEFINITION
# ============================================================================

class EVMCSVProcessor:
    """Process uploaded EVM CSV files"""
    # This docstring appears when you do help(EVMCSVProcessor)

    REQUIRED_COLUMNS = [
        'Control Account',  
        'Work Package',     
        'Resource',        
        'EOC',             
        'Results',         
        'IPT',             
        'CAM',             
        'Set Name',        
        'Date',            
        'Value'            
    ]
    

    def __init__(self, csv_file, upload_record, program):
        """
        Initialize the CSV processor
        
        Args:
            csv_file: Django File object (the uploaded CSV file)
            upload_record: CSVUpload model instance (tracks this upload in DB)
            program: Program model instance (which program this data belongs to)
        """
        # Save parameters to instance variables (self.x means "this object's x")
        self.csv_file = csv_file
        # The uploaded file - we'll read from this
        
        self.upload_record = upload_record
        # The database record tracking this upload
        # We'll update its status: pending → completed/failed
        
        self.program = program
        # Which program this data belongs to
        # Used when creating database records to link them to this program
        
        # Initialize tracking variables
        self.errors = []
        # List to store error details if rows fail
        # Example: [{'row': 5, 'error': 'Bad date', 'data': {...}}]
        
        self.rows_processed = 0
        # Counter: how many rows successfully saved to database
        
        self.rows_failed = 0
        # Counter: how many rows had errors
    

    def process(self):
    
        

        try:
            
            decoded_file = self.csv_file.read().decode('utf-8')
            # self.csv_file.read() → reads file as bytes: b'Control Account,Work Package...'
            # .decode('utf-8') → converts bytes to text: 'Control Account,Work Package...'
            # Result: decoded_file is a string containing the entire CSV as text
            
            io_string = io.StringIO(decoded_file)
            # Takes the text string and wraps it so it acts like a file
            # csv.DictReader expects a file object, not a plain string
            
            reader = csv.DictReader(io_string)
            # Creates a CSV parser that reads rows as dictionaries
            # First row becomes column names (keys)
            # Each subsequent row becomes a dictionary
            # Example: {'Control Account': 'CA1', 'Work Package': 'WP1', 'Value': '100'}
            
            if not self.validate_headers(reader.fieldnames):
                # reader.fieldnames = list of column headers from CSV
                # validate_headers() checks if all REQUIRED_COLUMNS exist
                # Returns False if any columns are missing
                
                # If validation failed, mark upload as failed and stop
                self.upload_record.status = 'failed'
                # Update the database record to show this upload failed
                
                self.upload_record.errors = self.errors
                # Save error messages to the database
                # (errors were added in validate_headers())
                
                self.upload_record.save()
                # Write changes to database
                
                return False
                # Exit early - no point continuing if CSV structure is wrong
            
            
            for row_num, row in enumerate(reader, start=2):
                # Loop through each row in the CSV
                # enumerate adds row numbers, starting at 2 (row 1 is headers)
                # row_num = 2, 3, 4, ... (which row we're on)
                # row = dictionary with this row's data
                
                try:
                    # Try to process this row
                    self.process_row(row, row_num)
                    # Calls process_row() to save this row to database
                    
                    self.rows_processed += 1
                    # If we get here, row processed successfully
                    # Increment success counter
                    
                except Exception as e:
                    # If process_row() raised an error, catch it here
                    # This means THIS row failed, but we continue with other rows
                    
                    self.rows_failed += 1
                    # Increment failure counter
                    
                    self.errors.append({
                        'row': row_num,           # Which row failed (e.g., row 5)
                        'error': str(e),          # What the error was
                        'data': row               # The actual row data
                    })
                    # Example: {'row': 5, 'error': 'Invalid date', 'data': {...}}
            

            
            self.upload_record.rows_total = self.rows_processed + self.rows_failed
            # Total rows attempted (successful + failed)
            
            self.upload_record.rows_processed = self.rows_processed
            # How many succeeded
            
            self.upload_record.rows_failed = self.rows_failed
            # How many failed
            
            self.upload_record.errors = self.errors
            # Full list of errors (if any)
            # Saved as JSON in database
            
            self.upload_record.status = 'completed'
            # Mark upload as complete
            
            self.upload_record.save()
            # Write all changes to database
            
            return True
            # Return success - processing complete
            
        except Exception as e:
            
            self.upload_record.status = 'failed'
            # Mark entire upload as failed
            
            self.upload_record.errors = [{'error': f'Fatal error: {str(e)}'}]
            # Save the fatal error message
            
            self.upload_record.save()
            # Write to database
            
            return False
            # Return failure
    

    def validate_headers(self, headers):
        """Check if CSV has all required columns"""
        # headers = list of column names from CSV
        # Example: ['Control Account', 'Work Package', 'Date', 'Value']
        
        missing = [col for col in self.REQUIRED_COLUMNS if col not in headers]
        # List comprehension: find columns that are required but missing
        # Breaking it down:
        #   for col in self.REQUIRED_COLUMNS:  # Loop through required columns
        #       if col not in headers:          # Is this column missing?
        #           missing.append(col)         # Add to missing list
        # Example result: ['EOC', 'IPT'] (these are missing from CSV)
        
        if missing:
            # If any columns are missing
            
            self.errors.append({
                'error': f'Missing required columns: {", ".join(missing)}'
            })
            # Add error message

            
            return False
            # Return False = validation failed
        
        return True
        # If we get here, all required columns exist
        # Return True = validation passed
    

    @transaction.atomic
    # This decorator makes the entire method one database transaction
    # If ANY part fails, ALL database changes are rolled back
    # Example: If we create ControlAccount but EVMData fails,
    #          the ControlAccount gets deleted too (rolled back)
    def process_row(self, row, row_num):
        """Process a single CSV row and save to database"""
        # row = dictionary with this row's data
        # row_num = which row number (for error messages)
        
        
        ca_name = row['Control Account'].strip()
        # Get 'Control Account' value and remove whitespace
        
        wp_name = row['Work Package'].strip()
        # Get 'Work Package' value
        
        resource = row.get('Resource', '').strip()
        # Get 'Resource' value, return empty string if missing

        
        eoc = row['EOC'].strip()
        # Element of Cost (Labor, Material, ODC, PCL)
        
        results = row['Results'].strip()
        # Unit type (Dollars, Hours, FTE, Direct)
        
        ipt = row['IPT'].strip()
        # Integrated Product Team (Operations, Finance, Marketing, etc)
        
        cam = row['CAM'].strip()
        # Control Account Manager name
        
        cobra_set = row['Set Name'].strip()
        # Metric type (BCWS, BCWP, ACWP, EAC, etc)
        
        date_str = row['Date'].strip()
        
        value_str = row['Value'].strip()
    
        

        
        if not ca_name:
            # If Control Account name is empty
            raise ValueError('Control Account name is required')
            # Stop processing this row and throw error
            # Error gets caught in process() method at line with "except Exception as e"
        
        if not cobra_set:
            # If metric type is empty
            raise ValueError('Set Name (metric type) is required')
            # Stop processing this row
        

        
        ca, created = ControlAccount.objects.get_or_create(
            # This does two things:
            # 1. Tries to find existing ControlAccount matching these criteria
            # 2. If not found, creates a new one
            
            program=self.program,
            # Must belong to this program
            
            ca_name=ca_name,
            # Must have this name
            
            defaults={'cam': cam, 'ipt': ipt}
            # If creating new, use these values for cam and ipt
            # If found existing, these are ignored
        )
        # Returns:
        #   ca = the ControlAccount object (existing or new)
        #   created = True if new, False if existing
        
        # What Django does:
        # 1. SELECT * FROM control_accounts WHERE program_id=5 AND ca_name='CA1'
        # 2. If found: return existing record
        # 3. If not found: INSERT INTO control_accounts (...) VALUES (...)
        

        
        wp = None
        # Initialize as None (no work package yet)
        
        if wp_name:
            # Only create WorkPackage if name exists in CSV
            # (Work Package is optional - some rows might not have one)
            
            wp, created = WorkPackage.objects.get_or_create(
                # Same pattern as ControlAccount
                
                control_account=ca,
                # Must belong to the ControlAccount we just got/created
                
                wp_name=wp_name
                # Must have this name
            )
            # wp = the WorkPackage object
            # If wp_name was empty, wp stays None
        

        
        date = self.parse_date(date_str)
        # Convert date string to Python date object
        # Example: '1/15/2024' → datetime.date(2024, 1, 15)
        # Calls parse_date() method below
        
        value = self.parse_decimal(value_str)
        # Convert value string to Decimal number
        # Example: '$1,234.56' → Decimal('1234.56')
        # Calls parse_decimal() method below
        
       
        EVMData.objects.create(
            # Creates one row in the evm_data database table
            # Django generates SQL: INSERT INTO evm_data (...) VALUES (...)
            program=self.program,
        
            
            control_account=ca,
            # Link to ControlAccount (the one we got/created above)
            
            work_package=wp,
            # Link to WorkPackage (or None if no work package)
            
            resource=resource,
            # Employee/contractor name (can be empty)
            
            eoc=eoc,
            # Element of Cost
            
            results=results,
            # Unit type
            
            ipt=ipt,
            # Integrated Product Team
            
            cam=cam,
            # Control Account Manager name
            
            cobra_set=cobra_set,
            # BCWS, BCWP, ACWP, EAC, etc
            
            date=date,
            # The parsed date object
            
            value=value,
            # The parsed Decimal number
            
            csv_upload=self.upload_record
            # Link to the upload record (audit trail - which upload created this data)
        )

    

    def parse_date(self, date_str):
        """Convert date string to Python date object"""
        # date_str = string like '1/15/2024' or '2024-01-15'
        
        # Try format 1: M/D/YYYY (American format)
        try:
            return datetime.strptime(date_str, '%m/%d/%Y').date()
            # datetime.strptime = "string parse time"
            # %m = month (01-12), %d = day (01-31), %Y = year (2024)
            # Example: '1/15/2024' → datetime.date(2024, 1, 15)
            # .date() extracts just the date part (no time)
            # If successful, return immediately
            
        except ValueError:
            # If format doesn't match, ValueError is raised
            pass
            # Ignore error and continue to next format
        
        # Try format 2: YYYY-MM-DD (ISO format)
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
            # Example: '2024-01-15' → datetime.date(2024, 1, 15)
            # If successful, return immediately
            
        except ValueError:
            # If this format doesn't match either
            pass
            # Ignore and continue
        
        # If we get here, both formats failed
        raise ValueError(f'Invalid date format: {date_str}')
        # Raise error - this will be caught in process() method
        # User will see: "Row 5: Invalid date format: 13/45/2024"
    

    def parse_decimal(self, value_str):
        """Convert value string to Decimal number"""
        # value_str = string like '100.50' or '$1,234.56' or '1,234'
        
        try:
            cleaned = str(value_str).replace('$', '').replace(',', '').strip()
            # Clean up the string:
            # 1. str(value_str) ensures it's a string (just in case)
            # 2. .replace('$', '') removes dollar signs: '$100' → '100'
            # 3. .replace(',', '') removes commas: '1,234' → '1234'
            # 4. .strip() removes whitespace: '  100  ' → '100'
            # Result: '$1,234.56' becomes '1234.56'
            
            return Decimal(cleaned) if cleaned else Decimal('0')
            # If cleaned string has content, convert to Decimal
            # If cleaned string is empty, return 0
            # Decimal('1234.56') → Decimal object with exact value
            # Why Decimal not float: avoids rounding errors in financial calculations
            
        except:
            # If conversion fails (e.g., 'abc' can't be converted to number)
            raise ValueError(f'Invalid numeric value: {value_str}')
            # Raise error - will be caught in process()
            # User will see: "Row 5: Invalid numeric value: abc"
