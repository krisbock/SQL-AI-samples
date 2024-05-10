# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/azureml/promptflow/promptflow-runtime-stable:latest

WORKDIR /

COPY ./promptflow/requirements.txt promptflow/requirements.txt

RUN apt-get update && apt-get install -y runit gcc

RUN curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
RUN  ACCEPT_EULA=Y apt-get install -y msodbcsql18
# optional: for bcp and sqlcmd

# create conda environment
RUN conda create -n promptflow-serve python=3.9.16 pip=23.0.1 -q -y && \
    conda run -n promptflow-serve \
    pip install -r /promptflow/requirements.txt && \
    conda run -n promptflow-serve pip install keyrings.alt && \
    conda run -n promptflow-serve pip install gunicorn==20.1.0 && \
    #conda run -n promptflow-serve pip cache purge && \
    conda clean -a -y

COPY ./promptflow promptflow

EXPOSE 8080

#COPY ./connections/* /connections/

# reset runsvdir
#RUN rm -rf /var/runit
#COPY ./runit /var/runit
# grant permission
#RUN chmod -R +x /var/runit

#COPY ./start.sh /
#CMD ["bash", "./start.sh"]