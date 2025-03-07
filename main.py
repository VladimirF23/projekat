#proverava da li se skripta pokrece direktno tj kao main program ili je importovana kao moduo u drugoj skripti
#ako se direktno ranuje onda se ovo dole executuje, app.run pokrece Flask development server i pokrece web app

from flask import Flask
from Backend.API import *
import threading
#treba dodati react file ovde
app = Flask(__name__)



app.register_blueprint(registration_blueprint)

if __name__ =='__main__':
    app.run(debug=True, threaded=True)     #debug ->autoReload ako je promena u python code-u server se automatski restartuje, i debug console koju flask pokaze ako dodje do errora