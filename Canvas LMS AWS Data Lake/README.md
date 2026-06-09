# Canvas LMS to AWS Serverless Data Lake 🚀

An end-to-end Data Engineering pipeline that extracts academic and operational data from Canvas LMS via REST API, orchestrates the transformation using Apache Spark, and builds a highly queried Data Lakehouse on AWS.

## 🏗️ Architecture Overview

This project implements a Serverless ETL architecture designed for scalability, low maintenance, and cost-efficiency.

1. **Extract (EL):** A Python script interacts with the Canvas LMS API (handling pagination and authentication) to extract raw JSON course data and loads it directly into an Amazon S3 "Raw" bucket.
2. **Transform (T):** An AWS Glue job running PySpark reads the raw JSON, enforces a strict schema, cleanses the data (handling nulls and casting data types), and adds ETL metadata.
3. **Load (L):** The transformed data is written back to an Amazon S3 "Processed" bucket in **Parquet format**, partitioned by `subaccount_id` and `workflow_state` to optimize query performance.
4. **Analytics:** Amazon Athena is used to run serverless SQL queries directly against the partitioned Parquet files for immediate academic insights and ERP integration audits.

## 🛠️ Tech Stack

* **Source System:** Canvas LMS REST API
* **Cloud Provider:** Amazon Web Services (AWS)
* **Storage:** Amazon S3 (Raw & Processed Zones)
* **Compute / ETL:** AWS Glue (PySpark), AWS Lambda
* **Data Cataloging & Querying:** AWS Glue Data Catalog, Amazon Athena
* **Language:** Python 3.12, SQL

## 📂 Repository Structure

* `/extract`: Contains the Python integration code (`extract_canvas_api.py`) using `boto3` and `requests`.
* `/transform`: Contains the PySpark ETL job (`glue_clean_pyspark.py`).
* `/docs`: Architecture diagrams and workflow documentation.
* `/querys/athena_queries.sql`: Sample analytical queries for LMS auditing.

## 🔐 Security & Best Practices Implemented

* **Secret Management:** API tokens and sensitive keys are handled via environment variables (designed for AWS Secrets Manager integration in production).
* **Columnar Storage:** Usage of Apache Parquet reduces S3 storage costs and Athena query scanning times by up to 90%.
* **Smart Partitioning:** Data is hierarchically partitioned, preventing full-table scans during analytics.