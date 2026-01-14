FROM python:3.9
WORKDIR /app
COPY ./requirements.txt /app/
RUN pip install -r /app/requirements.txt
COPY run.sh /app/
ENV PYTHONPATH /app
ENV PATH $PATH:/app
RUN chmod 755 /app/run.sh
CMD /app/run.sh
