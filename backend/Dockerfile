# Backend image: FastAPI + pyodbc (ODBC Driver 17) + matplotlib/reportlab.
# Pin to Debian 12 (bookworm): the Microsoft ODBC repo below targets debian/12,
# and the default python:3.13-slim has since moved to Debian 13 (trixie).
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: build tools for pyodbc + the Microsoft ODBC Driver 17.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl gnupg2 apt-transport-https ca-certificates gcc g++ unixodbc-dev \
 && curl -sSL -O https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
 && dpkg -i packages-microsoft-prod.deb \
 && rm packages-microsoft-prod.deb \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

# Single worker so the APScheduler instance is not duplicated (see DEFECTS D41).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
