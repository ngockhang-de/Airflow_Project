## Recovery Plan

The BrightCart Daily Sales Pipeline is designed to recover safely from failures without losing raw data or creating duplicate sales reports.

### 1. Failure Scenarios and Recovery Actions

| Failure scenario | Recovery action |
|---|---|
| Missing or corrupted input files | Stop the pipeline and check whether both customer and order files are available and readable. Re-upload or replace the incorrect files before rerunning. |
| Data validation failure | Keep invalid records in the rejected output with rejection reasons. Review the rejected records and correct the source data if necessary. |
| Transformation task failure | Check the Airflow task logs, identify the error, fix the issue, and retry the failed task. |
| Daily sales report generation failure | Rerun the report generation task after confirming that validated input data is available. |
| Airflow DAG failure | Inspect the failed task in the Airflow UI, review logs, resolve the issue, and clear/retry the failed task. |

### 2. Recovery Procedure

If a pipeline run fails, the following steps are performed:

1. Open the Airflow UI and identify the failed task.
2. Check the task logs to understand the cause of the failure.
3. Verify that the original raw input files are still available and unchanged.
4. Fix the underlying issue, such as missing files, incorrect data formats, or transformation errors.
5. Retry the failed task or rerun the DAG if necessary.
6. Verify that valid and rejected records are generated correctly.
7. Check the audit record to confirm that source, valid, and rejected record counts reconcile.
8. Confirm that the final daily sales report has been generated successfully.

### 3. Data Safety and Idempotency

To prevent data loss and duplication:

- Raw input files are preserved and are never overwritten during processing.
- Rejected records are stored separately with clear rejection reasons.
- Processing the same input data again should not create duplicate records in the final sales report.
- Output files should be replaced or regenerated for the relevant processing date rather than blindly appended.
- Audit information is maintained to track processing results and record counts.

### 4. Recovery Validation

After recovery, the pipeline must pass the following checks:

- All expected input files are available.
- Source record counts match the sum of valid and rejected records.
- Valid and rejected outputs are generated successfully.
- The daily sales report exists and contains the expected results.
- Revenue calculations are correct.
- The Airflow DAG run finishes with a successful status.

**Expected result:** The pipeline can recover from failures without losing raw data, silently dropping invalid records, or producing duplicate sales results.
