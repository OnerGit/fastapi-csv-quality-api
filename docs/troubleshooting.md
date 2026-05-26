# Troubleshooting

This document collects common issues when running the FastAPI CSV Quality API locally on Windows, with Docker, or with sample CSV files.

## 1. PowerShell `curl` behaves differently from expected

### Symptom

The command looks correct, but PowerShell returns unexpected parameter errors or does not send the multipart file upload correctly.

### Cause

On Windows PowerShell, `curl` may be treated as an alias instead of the native curl executable.

### Fix

Use `curl.exe` explicitly:

```powershell
curl.exe http://127.0.0.1:8000/health
```

For file upload:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/analyze" `
  -F "file=@sample_data/bad_sample.csv"
```

With expected columns:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/analyze" `
  -F "file=@sample_data/bad_sample.csv" `
  -F "expected_columns=id,name,email,age,country"
```

## 2. Port 8000 is already in use

### Symptom

When starting the local server or Docker container, you may see an error similar to:

```text
address already in use
```

or:

```text
Bind for 0.0.0.0:8000 failed: port is already allocated
```

### Cause

Another process or container is already using port `8000`.

### Fix for local Uvicorn

Use another port:

```powershell
uvicorn app.main:app --reload --port 8001
```

Then open:

```text
http://127.0.0.1:8001/docs
```

### Fix for Docker

Check running containers:

```powershell
docker ps
```

Stop the container that uses port 8000:

```powershell
docker stop <container_id>
```

Or map the container to another host port:

```powershell
docker run --rm -p 8001:8000 fastapi-csv-quality-api:0.1.0
```

Then open:

```text
http://127.0.0.1:8001/docs
```

## 3. Docker Desktop is not running

### Symptom

The Docker build or run command fails with an error similar to:

```text
error during connect
```

or:

```text
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

### Cause

Docker Desktop is not running, or the Linux container engine is not available.

### Fix

Start Docker Desktop from the Windows Start menu and wait until the engine is running.

Then verify Docker:

```powershell
docker version
```

You should see both `Client` and `Server` sections.

If Docker still does not respond, restart WSL:

```powershell
wsl --shutdown
```

Then start Docker Desktop again.

## 4. Docker build is slow

### Symptom

The first Docker build takes several minutes.

### Cause

The image needs to pull the Python base image and install Python dependencies such as FastAPI, pandas, and Uvicorn.

### Fix

This is expected for the first build. Later builds are usually faster because Docker can reuse cached layers.

Run:

```powershell
docker build -t fastapi-csv-quality-api:0.1.0 .
```

## 5. CSV parse error

### Symptom

The `/analyze` endpoint returns a structured error response for an uploaded CSV file.

### Possible causes

- The file is not a valid CSV.
- The file has inconsistent delimiters.
- The file encoding is not UTF-8.
- The file is empty or has no readable data.

### Fix

Try one of the included sample files first:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/analyze" `
  -F "file=@sample_data/good_sample.csv"
```

Then test your own CSV file after confirming the API works.

## 6. File is larger than 5 MB

### Symptom

The API returns an error similar to:

```json
{
  "error": {
    "code": "file_too_large",
    "message": "Uploaded file is too large. Maximum supported size is 5 MB."
  }
}
```

### Cause

This MVP intentionally limits upload size to keep the project simple and predictable for local demos.

### Fix

Use a smaller CSV file for this demo project.

For production use, possible improvements include:

- streaming file processing
- background jobs
- object storage
- configurable upload limits
- chunk-based validation

These are intentionally out of scope for the current MVP.

## 7. Tests fail because dependencies are missing

### Symptom

Running tests returns an import error such as:

```text
ModuleNotFoundError: No module named 'fastapi'
```

### Cause

The virtual environment is not activated, or dependencies have not been installed.

### Fix

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run tests:

```powershell
python -m pytest
```

## 8. Swagger UI does not open

### Symptom

The browser cannot open:

```text
http://127.0.0.1:8000/docs
```

### Cause

The FastAPI application is not running, or it is running on a different port.

### Fix

Start the app:

```powershell
uvicorn app.main:app --reload
```

If you use a different port:

```powershell
uvicorn app.main:app --reload --port 8001
```

Then open:

```text
http://127.0.0.1:8001/docs
```