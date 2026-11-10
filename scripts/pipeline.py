import json
import os
from pathlib import Path

import pandas as pd
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

COMPLETED_STATUS = "COMPLETED"


def check_raw_files(run_date):

    folder = os.path.join(DATA_DIR, "raw", run_date)

    required_files = [
        "orders.csv",
        "customers.csv"
    ]

    missing_files = []

    for file in required_files:
        file_path = os.path.join(folder, file)

        if not os.path.isfile(file_path):
            missing_files.append(file)

    if missing_files:
        raise FileNotFoundError(
            f"Missing files in {folder}: {missing_files}"
        )

    print(f"All files are available for {run_date}")

    return "clean_orders"


def validate_customers(raw_customers):
    customers = raw_customers.copy()

    customers["customer_name"] = (
        customers["customer_name"]
        .str.strip()
        .replace("", np.nan)
    )

    customers["city"] = (
        customers["city"]
        .str.strip()
        .str.title()
        .replace("", np.nan)
    )

    customers["customer_id"] = pd.to_numeric(
        customers["customer_id"],
        errors="coerce"
    ).astype("Int64")

    conditions = [
        customers["customer_id"].isna(),
        customers["customer_id"].le(0).fillna(False),
        customers["customer_name"].isna(),
        customers["city"].isna(),
        customers["customer_id"].duplicated(keep='first')
    ]

    reasons = [
        "missing_customer_id",
        "invalid_customer_id",
        "missing_customer_name",
        "missing_city",
        "duplicate_customer_id"
    ]

    customers["rejection_reason"] = np.select(
        conditions,
        reasons,
        default="valid"
    )

    valid = customers[
        customers["rejection_reason"] == "valid"
    ].drop(columns="rejection_reason")

    rejected = customers[
        customers["rejection_reason"] != "valid"
    ]

    return valid, rejected


def standardise_orders(raw_orders):
    orders = raw_orders.copy()

    orders["status"] = orders["status"].str.strip().str.upper()
    orders["product_name"] = orders["product_name"].str.strip()
    orders["unit_price_gbp"] = orders["unit_price_gbp"].str.replace("£", "", regex=False)

    orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
    orders["unit_price_gbp"] = pd.to_numeric(orders["unit_price_gbp"], errors="coerce")
    orders["customer_id"] = pd.to_numeric(orders["customer_id"], errors="coerce").astype("Int64")

    iso_dates = pd.to_datetime(orders["order_date"], format="%Y-%m-%d", errors="coerce")
    uk_dates = pd.to_datetime(orders["order_date"], format="%d/%m/%Y", errors="coerce")
    orders["order_date"] = iso_dates.fillna(uk_dates)
    return orders



def validate_orders(orders):
    orders = orders.copy()

    valid_statuses = [
        "COMPLETED",
        "PENDING",
        "CANCELLED",
        "REFUNDED",
        "SHIPPED"
    ]

    checks = {
        "Missing required fields": (
            orders["customer_id"].isna() |
            orders["unit_price_gbp"].isna()
        ),

        "Invalid quantity": (
            orders["quantity"].notna() &
            (orders["quantity"] <= 0)
        ),

        "Invalid price": (
            orders["unit_price_gbp"].notna() &
            (orders["unit_price_gbp"] <= 0)
        ),

        "Invalid status": (
            orders["status"].notna() &
            ~orders["status"].isin(valid_statuses)
        ),

        "Empty product name": (
            orders["product_name"].str.strip().eq("").fillna(False)
        ),

        "Duplicate order ID": (
            orders["order_id"].notna() &
            orders["order_id"].duplicated(keep=False)
        ),

        "Invalid date": (
            orders["order_date"].notna() &
            (orders["order_date"] >
             pd.Timestamp.today().normalize())
        )
    }

    invalid_conditions = pd.Series(
        False, index=orders.index
    )

    for condition in checks.values():
        invalid_conditions |= condition

    orders["rejection_reason"] = ""

    for error, condition in checks.items():
        orders.loc[condition, "rejection_reason"] += (
            error + "; "
        )

    invalid_orders = orders[invalid_conditions].copy()
    valid_orders = orders[~invalid_conditions].copy()

    return valid_orders, invalid_orders


def enrich_orders(orders, customers):
    enriched_orders = orders.merge(
        customers[["customer_id", "customer_name", "city"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    enriched_orders['total_price_gbp'] = (
        enriched_orders['quantity'] * enriched_orders['unit_price_gbp']
    ).round(2)

    return enriched_orders


def clean_orders(run_date):
    output_dir = os.path.join(DATA_DIR, "cleaned", run_date)

    os.makedirs(output_dir, exist_ok=True)

    raw_orders_path = os.path.join(DATA_DIR, "raw", run_date, "orders.csv")
    raw_customers_path = os.path.join(DATA_DIR, "raw", run_date, "customers.csv")

    raw_orders = pd.read_csv(raw_orders_path)
    raw_customers = pd.read_csv(raw_customers_path)

    valid_customers, rejected_customers = validate_customers(raw_customers)
    standardised_orders = standardise_orders(raw_orders)
    valid_orders, rejected_orders = validate_orders(standardised_orders)
    enriched_orders = enrich_orders(valid_orders, valid_customers)

    valid_customers.to_csv(os.path.join(output_dir, "valid_customers.csv"), index=False)
    rejected_customers.to_csv(os.path.join(output_dir, "rejected_customers.csv"), index=False)

    enriched_orders.to_csv(os.path.join(output_dir, "valid_orders.csv"), index=False)
    rejected_orders.to_csv(os.path.join(output_dir, "rejected_orders.csv"), index=False)

    counts = {
        "customers_source": len(raw_customers),
        "customers_valid": len(valid_customers),
        "customers_rejected": len(rejected_customers),
        "orders_source": len(raw_orders),
        "orders_valid": len(enriched_orders),
        "orders_rejected": len(rejected_orders),
    }
    print(f"[{run_date}] Cleaned: {counts}")
    return counts


def build_city_summary(run_date):
    output_dir = os.path.join(DATA_DIR, "curated", run_date)

    os.makedirs(output_dir, exist_ok=True)

    raw_customers = pd.read_csv(os.path.join(DATA_DIR, "raw", run_date, "customers.csv"), dtype=str)
    raw_orders = pd.read_csv(os.path.join(DATA_DIR, "raw", run_date, "orders.csv"), dtype=str)
    valid_customers = pd.read_csv(os.path.join(DATA_DIR, "cleaned", run_date, "valid_customers.csv"))
    rejected_customers = pd.read_csv(os.path.join(DATA_DIR, "cleaned", run_date, "rejected_customers.csv"))
    orders = pd.read_csv(os.path.join(DATA_DIR, "cleaned", run_date, "valid_orders.csv"))
    rejected_orders = pd.read_csv(os.path.join(DATA_DIR, "cleaned", run_date, "rejected_orders.csv"))

    completed = orders[orders["status"] == COMPLETED_STATUS]

    city_sales = (
        completed
        .groupby("city", as_index=False)
        .agg(
            completed_orders=("order_id", "count"),
            completed_revenue_gbp=("total_price_gbp", "sum"),
        )
        .sort_values("completed_revenue_gbp", ascending=False)
    )

    top_order = completed.loc[completed["total_price_gbp"].idxmax()]
    completed_revenue = round(float(completed["total_price_gbp"].sum()), 2)

    daily_summary = pd.DataFrame([{
        "run_date": run_date,
        "completed_orders": len(completed),
        "completed_revenue_gbp": completed_revenue,
        "top_order_id": int(top_order["order_id"]),
        "top_order_revenue_gbp": float(top_order["total_price_gbp"]),
        "rejected_orders": len(rejected_orders),
    }])

    city_sales.to_csv(os.path.join(output_dir, "city_sales.csv"), index=False)
    daily_summary.to_csv(os.path.join(output_dir, "daily_summary.csv"),index=False)

    audit = {
        "run_date": run_date,
        "customers": {
            "source": len(raw_customers),
            "valid": len(valid_customers),
            "rejected": len(rejected_customers),
            "rejected_by_reason": rejected_customers["rejection_reason"].value_counts().to_dict(),
        },
        "orders": {
            "source": len(raw_orders),
            "valid": len(orders),
            "rejected": len(rejected_orders),
            "rejected_by_reason": rejected_orders["rejection_reason"].value_counts().to_dict(),
        },
        "output": {
            "completed_orders": int(len(completed)),
            "completed_revenue_gbp": completed_revenue,
            "cities_in_report": int(len(city_sales)),
        },
    }

    audit_json = os.path.join(DATA_DIR, "audit", f"{run_date}.json")
    with open(audit_json, 'w') as file:
        json.dump(audit, file, indent=4)

    print(f"[{run_date}] Completed revenue: £{completed_revenue} from {len(completed)} orders")
    return audit["output"]


def run_quality_check(run_date):

    output_dir = os.path.join(DATA_DIR, "curated", run_date)
    cleaned_dir = os.path.join(DATA_DIR, "cleaned", run_date)
    audit_path = os.path.join(DATA_DIR, "audit", f"{run_date}.json")

    required_files = [
        os.path.join(output_dir, "city_sales.csv"),
        os.path.join(output_dir, "daily_summary.csv"),
        os.path.join(cleaned_dir, "valid_orders.csv"),
        os.path.join(cleaned_dir, "rejected_orders.csv"),
        os.path.join(cleaned_dir, "valid_customers.csv"),
        os.path.join(cleaned_dir, "rejected_customers.csv"),
        audit_path,
    ]

    missing_files = []
    empty_files = []

    for file_path in required_files:

        if not os.path.isfile(file_path):
            missing_files.append(file_path)
            print("Missing output file: %s", file_path)

        elif os.path.getsize(file_path) == 0:
            empty_files.append(file_path)
            print("Empty output file: %s", file_path)

        else:
            print("File check passed: %s", file_path)

    if missing_files or empty_files:
        raise FileNotFoundError(
            f"Quality check FAILED for {run_date}. "
            f"Missing files: {missing_files}. "
            f"Empty files: {empty_files}."
        )

    with open(audit_path, "r", encoding="utf-8") as file:
        audit = json.load(file)

    reconciliation_errors = []

    for entity in ["customers", "orders"]:

        block = audit[entity]

        if block["source"] != block["valid"] + block["rejected"]:
            reconciliation_errors.append(entity)

    if reconciliation_errors:
        raise ValueError(
            f"Data reconciliation FAILED for: {reconciliation_errors}"
        )

    result = {
        "run_date": run_date,
        "files_checked": len(required_files),
        "missing_files": len(missing_files),
        "empty_files": len(empty_files),
        "reconciliation": "PASSED",
        "status": "PASSED",
    }

    print("Quality checks PASSED: %s", result)

    return result
