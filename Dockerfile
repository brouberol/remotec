FROM python:3.5-slim
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
RUN groupadd user && useradd -g user user
COPY requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["api"]
COPY . /usr/src/app
USER user
