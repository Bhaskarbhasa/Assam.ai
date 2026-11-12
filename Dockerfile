FROM python:3.11-slim

WORKDIR /app

# Install system utilities for Linux hardware inspection (Problem 2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    pciutils \
    dmidecode \
    util-linux \
    procps \
    sudo \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

CMD ["streamlit", "run", "web_dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
