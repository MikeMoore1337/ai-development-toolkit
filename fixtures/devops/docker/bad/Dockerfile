# Deliberately broken synthetic Dockerfile. DO NOT EXECUTE.
FROM python:3.12-slim
WORKDIR /srv
COPY . /srv
USER root
EXPOSE 8080
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9090/health', timeout=2)"
CMD ["python", "/srv/missing.py"]
