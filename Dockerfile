# Basic docker image for Map-a-Droid
# Usage:
#   docker build -t MAD                   # Build the docker Image
#   docker run -d MAD startWalker.py -os  # Launch Walker 
#   docker run -d MAD startWalker.py -os  # Launch Screenshot Processing
#   docker run -d MAD madmin.py           # Launch MAdmin

FROM python:2.7-slim

# Default port the webserver runs on
EXPOSE 5000

# Working directory for the application
WORKDIR /usr/src/app

# Set Entrypoint with hard-coded options
ENTRYPOINT ["python"]
CMD ["./startWalker.py"] 

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends libgeos-dev build-essential
RUN apt-get update && apt-get -y install libglib2.0-0
RUN apt-get -y install tk
RUN apt-get update

COPY requirements.txt /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt

# RUN apt-get install libgtk2.0-dev -y

# Copy everything to the working directory (Python files, templates, config) in one go.
COPY . /usr/src/app/
