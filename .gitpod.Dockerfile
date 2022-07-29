FROM gitpod/workspace-full-vnc

RUN sudo apt-get update && \
    sudo apt-get install -y libx11-dev libxkbfile-dev libsecret-1-dev libnss3 libgbm-dev && \
    sudo rm -rf /var/lib/apt/lists/*

RUN pip install playwright pyodbc PyPDF2 requests bs4 pycryptodome pandas lxml \
    && playwright install