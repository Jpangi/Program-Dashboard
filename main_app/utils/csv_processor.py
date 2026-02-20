import csv
import io
from decimal import Decimal
from datetime import datetime
from main_app.models import Program, DataSnapshot
from django.db import transaction



# with open('media/uploads/Program_data.csv') as f:
#     reader = csv.reader(f)
#     for row in reader:
#         _, created = Teacher.objects.get_or_create(
#             first_name=row[0],
#             last_name=row[1],
#             middle_name=row[2],
#             )

