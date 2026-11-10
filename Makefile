run:
	airflow standalone

password:
	cat ~/airflow/simple_auth_manager_passwords.json.generated

errors:
	airflow dags list-import-errors

dag:
	export AIRFLOW__CORE__DAGS_FOLDER=/Users/ngockhangvu/Desktop/Airflow_Project/dags