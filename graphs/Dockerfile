#Grab the latest alpine image
FROM python:3.7-alpine


# Install python and pip
RUN apk update
RUN apk add --no-cache --update postgresql-dev gcc python3-dev musl-dev python3 py3-pip bash
ADD ./app/requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip3 install --no-cache-dir -q -r /tmp/requirements.txt

# Add our code
ADD ./app /opt/app/
WORKDIR /opt/app

# Expose is NOT supported by Heroku
# EXPOSE 5000

# Run the image as a non-root user
RUN adduser -D myuser
USER myuser

ENV heroku=1

# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku
CMD gunicorn --bind 0.0.0.0:$PORT wsgi

