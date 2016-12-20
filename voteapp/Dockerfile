FROM python:3.5

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD . /code/

RUN pip3 install -e git+https://github.com/iron-io/python-picassoclient.git#egg=picassoclient
RUN pip3 install -r /code/requirements.txt

ENTRYPOINT ["python3", "app.py"]
EXPOSE 9999
