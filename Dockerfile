FROM python:3.9.7-slim
ENV PYTHONUNBUFFERED 1
RUN apk update && apk add bash && apk add nano
RUN mkdir /src
WORKDIR /src
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /src/
CMD exec gunicorn my_energy.wsgi_docker:application --bind 0.0.0.0:8000 --workers 3

# build the image like this:
# docker build -t my_energy_mongo:latest .

# run the container from here, like this:
# cd ~/shared
# docker run -d --name my_energy_mongo --mount type=bind,source=$HOME/shared,target=/shared -p 8015:8000 --restart always my_energy_mongo:latest

# log into the container
# docker exec -it my_energy_mongo sh