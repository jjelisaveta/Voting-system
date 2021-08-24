FROM python:3

RUN mkdir -p /opt/src/user
WORKDIR /opt/src/user

COPY application/user/application.py ./application.py
COPY application/user/roleCheck.py ./roleCheck.py
COPY application/user/configuration.py ./configuration.py
COPY application/user/models.py ./models.py
COPY application/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/user"

ENTRYPOINT ["python", "./application.py"]