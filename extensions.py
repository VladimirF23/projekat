#da ne bi doslo do cirkularnog importa inicijalizujem app i ostale stvari ovde
from flask import Flask
from flask_jwt_extended import JWTManager
import redis
import os
from configJWT import Config            #moj config klass
from dotenv import load_dotenv


app = Flask(__name__)

app.config.from_object(Config)

load_dotenv(os.path.join(os.path.dirname(__file__), "devinfoDocker.env"))
redis_password = os.getenv("REDIS_PASSWORD")
#Redis localhost port je setupovan u Config-u  stavi ovo da se conectuje na redis conteiner
redis_client = redis.StrictRedis(
    host="redis",       #ime service
    port=6379,
    password= redis_password, 
    decode_responses=True  # Automatically decode strings
)


#Da proverimo redis dal se startovao
try:
    redis_client.ping()
    print("Connected to Redis successfully!")
except redis.ConnectionError:
    print("Failed to connect to Redis.")

jwt = JWTManager(app)

# Getter to use in other modules
def get_redis_client():
    return redis_client