FROM python


WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip3 install -r requirements.txt

COPY ./templates ./templates/
COPY ./static ./static/
COPY ./config.py .

COPY ./main.py .
COPY ./db.py .
COPY ./poker.py .


CMD [ "python3", "main.py" ] 
