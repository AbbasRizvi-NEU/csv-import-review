# CSV Import Review

A Python web app for reviewing an inventory spreadsheet before saving it. Upload a CSV to see which rows can be imported and why the others were rejected. Confirm the import to save valid rows in SQLite. Repeated SKUs already in the database are skipped, so reuploading a file keeps the original entries.

## Run locally

Use Python 3.12 and run these commands in PowerShell from the repository root.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --port 8011
```

1. Open [the import page](http://127.0.0.1:8011/) and upload `demo.csv`. The preview shows two valid rows and two rejected rows.
2. Choose **Import valid rows**. The app saves two items in `inventory.sqlite3`.
3. Upload and confirm the same file again. The app reports zero inserted and two already saved.

The demo accepts UTF-8 CSV files up to 64 KiB and 200 data rows. The columns are `sku,name,quantity`. SKUs are compared in uppercase, and the first valid row for each SKU in the file is eligible. An existing SKU keeps its saved name and quantity. The preview does not write to the database. Confirmation validates the CSV again and saves eligible rows in a transaction.

## Run the tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest -v
```

Portfolio project by [AbbasRizvi-NEU](https://github.com/AbbasRizvi-NEU), built with Codex assistance. The sample inventory is fictional. The app uses [FastAPI](https://github.com/fastapi/fastapi), [Uvicorn](https://github.com/Kludex/uvicorn), and [Python Multipart](https://github.com/Kludex/python-multipart) as separately installed dependencies.
