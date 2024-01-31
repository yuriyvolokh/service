FROM python:3.8
COPY requirements.txt ./
RUN pip install -r requirements.txt
EXPOSE 5000
COPY static ./
COPY database.db ./
COPY main.py ./
ENTRYPOINT python3.8 main.py
