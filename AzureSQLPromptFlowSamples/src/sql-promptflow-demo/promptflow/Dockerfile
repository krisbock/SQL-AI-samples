FROM mcr.microsoft.com/azureml/promptflow/promptflow-runtime-stable:latest
COPY ./* /

RUN curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18
RUN pip install -r requirements.txt

EXPOSE 8080