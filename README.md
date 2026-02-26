# Program-Dashboard

A full-stack web application for Earned Value Management (EVM) tracking. Program managers can create programs, upload CSV data exports, and visualize cost and schedule performance through interactive charts and dashboards.

Link to project: Live Demo

## How It's Made:
**Tech used:** Python, Django, SQL, Chart.js, HTML/CSS

### Frontend
The frontend is built with Django's templating engine and styled with custom CSS, creating a clean and professional dashboard experience. Django's URL routing handles navigation between pages including login, signup, program list, program detail, and CSV upload views.

For data visualization, I integrated Chart.js to display EVM performance data over time. The bar chart renders stacked data broken down by IPT (Integrated Product Team), with dropdown selectors to dynamically switch between different COBRA set types (BCWS, BCWP, ACWP) and result types (FTE, Dollars, Direct) without reloading the page.

### Backend
The backend is powered by Django running on Python. I implemented Django's built-in authentication system to secure user sessions and protect views with the `@login_required` decorator and `LoginRequiredMixin`. 

CSV data is processed through a custom `EVMCSVProcessor` utility class. When a user uploads a file, the backend validates required column headers, parses each row, and creates or retrieves the appropriate `ControlAccount` and `WorkPackage` records using `get_or_create` before writing `EVMData` rows. The upload record tracks processing status and any row-level errors.

### Database
SQL stores all program, control account, work package, and EVM data. The schema follows a clear hierarchy: Program → ControlAccount → WorkPackage → EVMData. Aggregated performance metrics (CPI, SPI, BCWS, BCWP, ACWP, EAC) are computed dynamically using Django ORM `Sum` aggregations defined as model properties on the `Program` and `ControlAccount` models. The `EVMSnapshot` model stores pre-calculated monthly metrics to improve dashboard performance.

---

## Key Features
- **User Authentication:** Secure signup/login using Django's built-in auth framework
- **Program Management:** Create, update, and delete programs with period-of-performance tracking
- **CSV Upload:** Upload EVM data exports with header validation, row-level error tracking, and upload history
- **Performance Metrics:** Automatic calculation of CPI, SPI, CV, SV, EAC, and BAC at the program level
- **Data Visualization:** Stacked bar chart with dynamic filtering by COBRA set and result type
- **Responsive Design:** Clean, modern UI that works across devices


---

## Lessons Learned

### Technical Challenges
Building this project deepened my understanding of Django and how to structure computed fields as model properties. Writing CPI, SPI, and cumulative metrics directly on the `Program` model using `Sum` aggregations keeps business logic centralized and testable. I also learned how `get_or_create` simplifies CSV import logic by handling deduplication at the database level rather than in application code.

### Data Visualization
Working with Chart.js gave me experience in presenting financial data clearly. The challenge was aggregating multi-dimensional EVM data (by date, IPT, and metric type) into a structure that Chart.js stacked bar charts could consume. I solved this by building a nested `chart_data` dictionary on the server and serializing it to JSON once, then switching datasets client-side with JavaScript event listeners.

### Database Design
Designing the EVM schema taught me about hierarchical data relationships and when to use `ForeignKey` vs. embedding data. The Program → ControlAccount → WorkPackage → EVMData hierarchy. I also learned the value of `related_name` — being able to call `program.evm_data.filter(...)` made writing model properties straightforward.


---

## Installation & Setup


### Backend Setup
```bash
# Clone the repository
git clone <repo-url>
cd program-dashboard

# Install dependencies
pip install -r requirements.txt

# Create a .env file in the project root
DATABASE_URL=your_postgresql_connection_string
SECRET_KEY=your_django_secret_key

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

---

## CSV Format

Uploaded CSV files must include the following columns:

| Column | Description |
|---|---|
| Control Account | Control account name |
| Work Package | Work package name |
| Resource | Resource name (optional) |
| EOC | Element of Cost (Labor, Material, ODC, PCL) |
| Results | Unit type (Dollars, FTE, Hours, Direct) |
| IPT | Integrated Product Team |
| CAM | Control Account Manager |
| Set Name | COBRA set (BCWS, BCWP, ACWP, EAC, CEAC, BAC) |
| Date | Reporting date (M/D/YYYY or YYYY-MM-DD) |
| Value | Numeric value |

---

## Future Enhancements
- Control Account detail pages with individual performance metrics
- EVMSnapshot auto-generation after CSV upload
- Edit and delete individual EVM data records
- Custom date range filtering on charts
- Dark mode toggle
- Export performance reports to PDF

