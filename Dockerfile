FROM python:3.6

COPY ./requirements.txt /requirements.txt

RUN pip install -r requirements.txt

COPY . /exchange
WORKDIR /exchange

# default to continuous double auction.
ENV MECHANISM cda
# only meaningful frequent batch auction.
ENV INTERVAL 3

ENV EXCHANGE_PORT 9001

RUN chmod +x ./bin/entrypoint.sh

CMD bash ./bin/entrypoint.sh
