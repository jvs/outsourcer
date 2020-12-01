# For some projects, I prefer using Docker to venv / poetry / pipenv / etc.
FROM python:3.6

WORKDIR /workspace

COPY requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
