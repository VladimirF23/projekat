#base image nam je python
FROM  python:3.9-slim


#wokring directory u containeru
WORKDIR /usr/src/app
# Install system dependencies ovo nam treba za mysql
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*



#kopiram requirments u container u /app
COPY requirments.txt ./

#instaliramo sve dependency u requirmentu koje smo nap
RUN pip install --no-cache-dir -r requirments.txt

#kopiramo ceo projekat u container
COPY . .

#Exposujemo port na kom ce Flask app runovati
# Set environment variables for Flask


EXPOSE 5000

# Set entrypoint script to wait for MySQL
ENTRYPOINT ["/bin/bash", "./wait-for-mysql.sh"]

CMD ["python", "main.py"] 


#Step by step ovoga
#1.docker compose --env-file devinfoDocker.env up -d  -> govori Docker COmposu da ucita .env variable, builduje image koji vec ne postoje, startuje containere definisan u docker-composu
#2.docker compose startuje mysql_db, redis, flask-app kontejnere (servise) i daje im .env variable iz definfoDocker.env
#3.Docker compose builduje image sa DockerFile tj sa ovim fileom ovde, koristi python base image, postavi working directory installuje dependencije iz requirments.txt, Kopira code moj sav
# napravi wait.for-mysql.sh executable i postavi Entrypoint da ceka na skriptu
#4.Kontejner se startuje i pokrene skriptu wait.for i Entrypoint kickunuje tu, i onda ceka na mysql da bude spreman tako sto ga pinguje, na redis isto tako sto koristi netcat (nc)
#Kada su oba spremna runuje se app tj main.py, flask app se pokrene i ceka na portu 5000 

