pipenv install -r requirements.txt

pipenv run uvicorn app.main:app --reload --port 8000