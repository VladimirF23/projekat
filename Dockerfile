#base image nam je python
FROM  python:3.9-slim


#wokring directory u containeru
WORKDIR /usr/src/app
# Install system dependencies ovo nam treba za mysql
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*



#kopiram requirements u container u /app
COPY requirements.txt ./

#instaliramo sve dependency u requirmentu koje smo nap
RUN pip install --no-cache-dir -r requirements.txt

#kopiramo ceo projekat u container
COPY . .


#da skripta moze da se exceutuje u contianer-u za svaki slucaj, +x ->make this file executable
RUN chmod +x wait-for-mysql.sh


#Exposujemo port na kom ce Flask app runovati
EXPOSE 5000
EXPOSE 5678   
#debugpy port 5678

#Entrypoin u DockerFile-u definise default komandu koju izvrsava kontejner koji je pokrenut iz image-a (image-a kog pravi ovaj DockerFile)
#/bin/bash je intepreter za skriptu, ./wait-for-mysql.sh  je skripta koja se izvrsava
#u wait-for-mysql.sh se ceka da se mysql kontejner startuje i da bude SPREMAN za primanje konekcija
#i u wait-for-mysql.sh se pokrece flask aplikacija preko komande 'exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client main.py' 


# Set entrypoint script to wait for MySQL, 
ENTRYPOINT ["/bin/bash", "./wait-for-mysql.sh"]



#Step by step ovoga
#1.docker compose --env-file devinfoDocker.env up -d  -> govori Docker COmposu da ucita .env variable, builduje image koji vec ne postoje, startuje containere definisan u docker-composu
#2.docker compose startuje mysql_db, redis, flask-app kontejnere (servise) i daje im .env variable iz definfoDocker.env
#3.Docker compose builduje image sa DockerFile tj sa ovim fileom ovde, koristi python base image, postavi working directory installuje dependencije iz requirements.txt, Kopira code moj sav
# napravi wait.for-mysql.sh executable i postavi Entrypoint da ceka na skriptu
#4.Kontejner se startuje i pokrene skriptu wait.for i Entrypoint kickunuje tu, i onda ceka na mysql da bude spreman tako sto ga pinguje, na redis isto tako sto koristi netcat (nc)
#Kada su oba spremna runuje se app tj main.py, flask app se pokrene i ceka na portu 5000 

