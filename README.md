# Britmart Daily ETL Pipeline

## Project Overview

This project implements a daily ETL (Extract, Transform, Load) pipeline using **Apache Airflow** and **Python**.

The pipeline processes raw customer and order data, validates and cleans records, enriches orders with customer information, generates sales reports by city, and performs data quality checks.

The goal is to produce reliable, structured sales data and an audit report for each processing date.

## Technologies Used

- **Python** – data processing and transformation
- **Pandas** – data cleaning, validation, and aggregation
- **NumPy** – handling missing values and validation logic
- **Apache Airflow** – workflow orchestration
- **CSV** – raw and processed data storage
- **JSON** – audit reporting

## Project Structure

```text
Airflow_Project/
│
├── dags/
│   └── britmart_daily_schedule.py
│
├── data/
│   ├── raw/
│   │   └── YYYYMMDD/
│   │       ├── orders.csv
│   │       └── customers.csv
│   │
│   ├── cleaned/
│   │   └── YYYYMMDD/
│   │       ├── valid_orders.csv
│   │       ├── rejected_orders.csv
│   │       ├── valid_customers.csv
│   │       └── rejected_customers.csv
│   │
│   ├── curated/
│   │   └── YYYYMMDD/
│   │       ├── city_sales.csv
│   │       └── daily_summary.csv
│   │
│   └── audit/
│       └── YYYYMMDD.json
│
├── scripts/
│   └── pipeline.py
│
├── requirements.txt
└── README.md
```

## Pipeline Workflow

The ETL pipeline consists of four main tasks:

### 1. Check Raw Files

- Checks whether `orders.csv` and `customers.csv` exist.
- Stops the pipeline if required input files are missing.
- Proceeds to data cleaning when all files are available.

### 2. Clean and Validate Data

**Customer data:**
- Removes unnecessary whitespace.
- Standardises city names.
- Converts customer IDs to numeric values.
- Identifies missing or invalid customer IDs.
- Identifies missing customer names and cities.
- Detects duplicate customer IDs.

**Order data:**
- Standardises order statuses.
- Cleans product names and prices.
- Converts quantities and prices to numeric values.
- Supports multiple date formats.
- Checks required fields and invalid values.
- Detects duplicate order IDs.
- Rejects invalid records with a recorded rejection reason.

Valid orders are then enriched with customer names and city information.

### 3. Build City Sales Summary

- Selects orders with `COMPLETED` status.
- Calculates completed order counts by city.
- Calculates completed revenue by city.
- Identifies the highest-value completed order.
- Generates a daily summary report.

**Output files:**
- `city_sales.csv`
- `daily_summary.csv`

### 4. Data Quality Checks

The final task verifies that:

- All expected output files exist.
- Output files are not empty.
- The audit JSON file can be read.
- Customer and order record counts reconcile:

  `Source Records = Valid Records + Rejected Records`

The pipeline raises an error if a quality check fails.

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Airflow_Project
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Airflow

Set the Airflow DAG directory:

```bash
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
```

### 4. Run Airflow

```bash
make run
```

## Running the Pipeline

1. Place the daily input files in:

   ```text
   data/raw/YYYYMMDD/
   ```

2. Ensure both files are available:

   - `orders.csv`
   - `customers.csv`

3. Start the Airflow API server and scheduler.

4. Open the Airflow UI and locate the Britmart ETL DAG.

5. Trigger the DAG for the required processing date.

## Expected Outputs

| Output | Description |
|---|---|
| `valid_customers.csv` | Validated customer records |
| `rejected_customers.csv` | Rejected customer records and reasons |
| `valid_orders.csv` | Cleaned and enriched orders |
| `rejected_orders.csv` | Rejected order records and reasons |
| `city_sales.csv` | Completed sales grouped by city |
| `daily_summary.csv` | Daily sales summary |
| `YYYYMMDD.json` | Audit report and processing statistics |

## Data Quality and Reconciliation

The pipeline records source, valid, and rejected record counts for both customers and orders.

Example:

```json
{
  "customers": {
    "source": 100,
    "valid": 95,
    "rejected": 5
  },
  "orders": {
    "source": 500,
    "valid": 480,
    "rejected": 20
  }
}
```

These figures are illustrative. Actual counts depend on the input data.

## Key Features

- Automated daily ETL workflow using Apache Airflow.
- Data cleaning and standardisation.
- Validation and rejection of invalid records.
- Customer and order data enrichment.
- City-level sales aggregation.
- Daily revenue reporting.
- JSON audit logging.
- Automated data quality and reconciliation checks.
