#!/bin/bash
set -e

env #da vidim koje sve .env variable ova skripta vidi

#ova skripta zna za .env varbaible zato sto docker engine ih loaduje u dockerComposu ./devinfo... a docker 

: "${MYSQL_HOST?Need to set MYSQL_HOST}"                #ove moraju da postoje, ako ne postoje scripta ce izaci sa error mesageom
: "${REDIS_PASSWORD?Need to set REDIS_PASSWORD}"

#za mysql je 3306, mozda je security issue al kasnije cu ovo popraviti
MYSQL_PORT=3306
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

echo "⏳ Waiting for MySQL to be ready at $MYSQL_HOST:$MYSQL_PORT..."

# Wait for MySQL to respond
while ! mysqladmin ping -h"$MYSQL_HOST" -P"$MYSQL_PORT" --silent; do
    sleep 1
done
echo "✅ MySQL is up."

#echo "⏳ Waiting for Redis to be ready at $REDIS_HOST:$REDIS_PORT..."

#Cekamo Redis to respond
# while ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping | grep -q PONG; do
#     sleep 2
# done
# echo "✅ Redis is up."

# Startujemo Flask app
echo "🚀 Starting Flask app..."
#exec python main.py
exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client main.py              #debuger ima fora zasto mora ovako a ne preko onog  u main-u sto ceka kao

#prvo manuelno sa docker-compose up da napravis containere ako si removovao i onda pozoves debug onaj preko VS-a e tada moze da se debuguje