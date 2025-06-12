#da ne bi doslo do cirkularnog importa inicijalizujem app i ostale stvari ovde
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import redis
import os
from configJWT import Config            #moj config klass
from dotenv import load_dotenv


app = Flask(__name__)

app.config.from_object(Config)   #Config sadrzi parametre za jwt token, a dole skroz se kreira jwt preko JWTManager-a

# region CORSE podesavanje

# CORS Configuration za Development (via Nginx ili direct React Dev Server)
#
# Moj React app kada served via Nginx ce biti pristupan iz 'https://localhost'
# API call-ovi kao '/api/auth/login' ce biti slani iz 'https://localhost' ka 'https://localhost/api/'
# Sa strane Browser-a ovo je 'same-origin' request (isti protocol, host, i implicitni port 443)
#
# Ali ako je moj React app direktno expose-ovan na http://localhost:3000 (kao sto je jeste u docker-compose-u za development)
# and a developer or proxy hits that directly, requests could originate from there.
#
# Browser izvrsava OPTIONS 'preflight' request za 'complex' request-ove (e.g POST sa 'application/json' Content-Type ili custom headers like 'X-CSRF-TOKEN'). 
# Da bi ovaj preflight radio moj Flask app mora da odgovori sa CORS headers cak i za same-origin

# 'resources={r"/*": ...}'     applies CORS za sve rout-ove
# 'origins':                   Lista truste-ovanih client origin-a
# 'methods':                   Ekplicitno dozvolajvamo HTTP metode koje ce moj frontend koristiti
# 'allow_headers':             Vazno za header-e koje salje moj frontend (Content-Type, X-CSRF-Token)
# 'supports_credentials=True': Za HttpOnly cookie-e koji se salju i primaju
# endregion

CORS(app, resources={r"/*": {
    "origins": ["https://localhost", "http://localhost:3000"],          # Dozvoljavamo oba Nginx (HTTPS) i direct React dev server (HTTP)
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],             # Osiguravamo sve metode koriscene od strane frontend-a da budu dozvoljene
    "allow_headers": ["Content-Type", "Authorization", "X-CSRF-Token"], # Ekplicitno dozvoljavamo header-e koriscene u request-u
    "supports_credentials": True                                        # MORA True za cookies (ukljucuci HttpOnly JWTs and CSRF) da bi radili preko svih origins/ports
}})

# region
# --- CORS for Production Environment (Commented Out for Reference) ---
#
# In a production setup, if Nginx serves your built React static files directly AND proxies
# your Flask API, and both are under the *same domain and port* (e.g., 'https://yourdomain.com'),
# then all browser-based requests to your API will be 'same-origin'.
# In this scenario, **CORS headers are technically NOT strictly required** for the browser client.
#
# You would ONLY need CORS configured in production if:
# 1. You have *other* clients (e.g., mobile apps, other web apps on different domains/subdomains)
#    that need to consume your Flask API.
# 2. Your frontend is served from a *different origin* than your API (e.g., frontend on 'app.yourdomain.com',
#    API on 'api.yourdomain.com').
#
# If you DO need CORS in production (e.g., for multi-client access), it would look like this:
#
# # CORS(app, resources={r"/*": {
# #     "origins": ["https://yourdomain.com", "https://mobileapp.yourdomain.com"], # List ALL trusted origins
# #     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
# #     "allow_headers": ["Content-Type", "Authorization", "X-CSRF-Token"],
# #     "supports_credentials": True
# # }})

# endregion






load_dotenv(os.path.join(os.path.dirname(__file__), "devinfoDocker.env"))
redis_password = os.getenv("REDIS_PASSWORD")
#Redis localhost port je setupovan u Config-u  stavi ovo da se conectuje na redis conteiner
redis_client = redis.StrictRedis(
    host="redis",       #ime service
    port=6379,
    password= redis_password, 
    decode_responses=True  # Automatically decode strings da ne budu u byte-ovima
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