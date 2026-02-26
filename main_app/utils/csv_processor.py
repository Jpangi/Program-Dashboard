import csv
import io
from decimal import Decimal
from datetime import datetime
from django.db import transaction

from main_app.models import Program, ControlAccount, WorkPackage, EVMData


class EVMCSVProcessor:
    """Process uploaded EVM CSV files"""

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
        self.csv_file = csv_file
        self.upload_record = upload_record
        self.program = program
        self.errors = []
        self.rows_processed = 0
        self.rows_failed = 0

    def process(self):
        try:
            # Decode file bytes to text and wrap in a file-like object for csv.DictReader
            decoded_file = self.csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            if not self.validate_headers(reader.fieldnames):
                self.upload_record.status = 'failed'
                self.upload_record.errors = self.errors
                self.upload_record.save()
                return False

            for row_num, row in enumerate(reader, start=2):
                try:
                    self.process_row(row, row_num)
                    self.rows_processed += 1
                except Exception as e:
                    self.rows_failed += 1
                    self.errors.append({
                        'row': row_num,
                        'error': str(e),
                        'data': row
                    })

            self.upload_record.rows_total = self.rows_processed + self.rows_failed
            self.upload_record.rows_processed = self.rows_processed
            self.upload_record.rows_failed = self.rows_failed
            self.upload_record.errors = self.errors
            self.upload_record.status = 'completed'
            self.upload_record.save()
            return True

        except Exception as e:
            self.upload_record.status = 'failed'
            self.upload_record.errors = [{'error': f'Fatal error: {str(e)}'}]
            self.upload_record.save()
            return False

    def validate_headers(self, headers):
        """Check if CSV has all required columns"""
        missing = [col for col in self.REQUIRED_COLUMNS if col not in headers]

        if missing:
            self.errors.append({
                'error': f'Missing required columns: {", ".join(missing)}'
            })
            return False

        return True

    @transaction.atomic
    def process_row(self, row, row_num):
        """Process a single CSV row and save to database"""
        ca_name = row['Control Account'].strip()
        wp_name = row['Work Package'].strip()
        resource = row.get('Resource', '').strip()
        eoc = row['EOC'].strip()
        results = row['Results'].strip()
        ipt = row['IPT'].strip()
        cam = row['CAM'].strip()
        cobra_set = row['Set Name'].strip()
        date_str = row['Date'].strip()
        value_str = row['Value'].strip()

        if not ca_name:
            raise ValueError('Control Account name is required')

        if not cobra_set:
            raise ValueError('Set Name (metric type) is required')

        # Get or create ControlAccount for this program
        ca, created = ControlAccount.objects.get_or_create(
            program=self.program,
            ca_name=ca_name,
            defaults={'cam': cam, 'ipt': ipt}
        )

        # Get or create WorkPackage if one was provided
        wp = None
        if wp_name:
            wp, created = WorkPackage.objects.get_or_create(
                control_account=ca,
                wp_name=wp_name
            )

        date = self.parse_date(date_str)
        value = self.parse_decimal(value_str)

        EVMData.objects.create(
            program=self.program,
            control_account=ca,
            work_package=wp,
            resource=resource,
            eoc=eoc,
            results=results,
            ipt=ipt,
            cam=cam,
            cobra_set=cobra_set,
            date=date,
            value=value,
            csv_upload=self.upload_record
        )

    def parse_date(self, date_str):
        """Convert date string to Python date object. Accepts M/D/YYYY or YYYY-MM-DD."""
        for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f'Invalid date format: {date_str}')

    def parse_decimal(self, value_str):
        """Convert value string to Decimal, stripping $ and commas."""
        try:
            cleaned = str(value_str).replace('$', '').replace(',', '').strip()
            return Decimal(cleaned) if cleaned else Decimal('0')
        except Exception:
            raise ValueError(f'Invalid numeric value: {value_str}')