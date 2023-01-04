FROM umihico/aws-lambda-selenium-python:latest



WORKDIR /var/task

COPY . /var/task/
RUN python -m pip install -r requirements.txt
CMD [ "main.handler" ]