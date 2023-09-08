FROM python:3.11

WORKDIR "/app"
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
ENV PYTHONPATH "${PYTHONPATH}:/app"
COPY . .
CMD ["python", "app/main.py"]