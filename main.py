#proverava da li se skripta pokrece direktno tj kao main program ili je importovana kao moduo u drugoj skripti
#ako se direktno ranuje onda se ovo dole executuje, app.run pokrece Flask development server i pokrece web app

from flask import Flask
from flask_jwt_extended import JWTManager
from Backend.API import *
import threading
import redis

from configJWT import Config            #moj config klass

#treba dodati react file ovde
app = Flask(__name__)

app.config.from_object(Config)

#Redis localhost port je setupovan u Config-u
redis_client = redis.StrictRedis.from_url(app.config["REDIS_URL"])

#JWT, JSON web token
jwt = JWTManager(app)

#NE ZABORAVI DA REGISTUJES BLUEPRINTOVE !
app.register_blueprint(registration_blueprint)
app.register_blueprint(auth_blueprint)

if __name__ =='__main__':
    app.run(debug=True, threaded=True)     #debug ->autoReload ako je promena u python code-u server se automatski restartuje, i debug console koju flask pokaze ako dodje do errora