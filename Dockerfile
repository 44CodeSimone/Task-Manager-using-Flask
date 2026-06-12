FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY todo_project ./todo_project

EXPOSE 5000

ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

CMD ["python", "todo_project/run.py"]
