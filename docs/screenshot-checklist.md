# Screenshot Checklist

Capture these after the project runs locally on Windows 11:

1. Swagger UI at `http://127.0.0.1:8000/docs`
2. `/health` response in Swagger or terminal
3. `/analyze` upload form in Swagger
4. JSON quality report for `sample_data/bad_sample.csv`
5. `pytest` passed in PowerShell
6. `docker build -t fastapi-csv-quality-api .`
7. `docker run --rm -p 8000:8000 fastapi-csv-quality-api`
8. GitHub repository homepage
9. README rendered on GitHub
