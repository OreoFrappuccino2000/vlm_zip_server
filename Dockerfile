FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "zip_to_image_files:app", "--host", "0.0.0.0", "--port", "8000"]
