FROM python:3.5-slim

# Setup project layour
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
RUN groupadd user && useradd -g user user

# Install requirements
COPY requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# Configure entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# Add the code in the end, to reduce the build time
COPY . /usr/src/app
USER user
