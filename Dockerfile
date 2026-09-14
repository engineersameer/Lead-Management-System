# From tells Docker which base image to use for the container. In this case, we are using the official Python 3.14 slim image.
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# 0.0.0.0 Means that the server will be accessible from any IP address, not just localhost. This is important for Docker containers, as they run in isolated environments.