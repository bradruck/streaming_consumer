FROM python:3.9
MAINTAINER Data Engineering Analytics Platform (DEAP)

#Create workdirectory & add application files
WORKDIR /src
ADD __init__.py /src

ADD requirements.txt /src
ADD config.ini /src
ADD config.py /src

ADD main.py /src
ADD api_key_tools.py /src
ADD oci_consumer_tools.py /src
ADD s3_tools.py /src
ADD file_management.py /src

RUN mkdir -p /src/api_keys
RUN mkdir -p /src/tmp

# Install App or Python Libraries
RUN pip install --upgrade pip
RUN pip install -r /src/requirements.txt

# Add user to run application
RUN groupadd -r -g 1001 appuser
RUN useradd -ms /bin/bash -r -u 1001 -g appuser appuser

# Grant root directory access to appuser
RUN chown -R appuser:appuser /src
USER 1001

#ENV to store logs in stdout
ENV PYTHONUNBUFFERED=0

ENTRYPOINT ["python", "/src/main.py"]
