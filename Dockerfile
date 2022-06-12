FROM python:3.9
COPY . /app
ENV PYTHONPATH=/app
RUN pip install -r /app/requirements.txt
CMD ["python", "/app/manage.py", "runserver", "0.0.0.0:8000"]
