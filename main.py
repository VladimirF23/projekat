#proverava da li se skripta pokrece direktno tj kao main program ili je importovana kao moduo u drugoj skripti
#ako se direktno ranuje onda se ovo dole executuje, app.run pokrece Flask development server i pokrece web app

from extensions import app, jwt, redis_client  # Umesto kreiranja novih objekata, uvozi ih
from Backend.API import *
import debugpy

#debugpy.listen(("0.0.0.0", 5678))
# Optional: wait for the debugger to attach before continuing
#debugpy.wait_for_client()

#NE ZABORAVI DA REGISTUJES BLUEPRINTOVE !
app.register_blueprint(registration_blueprint)
app.register_blueprint(auth_blueprint)

if __name__ =='__main__':
    app.run(host='0.0.0.0', port=5000,debug=True, threaded=True)#debug ->autoReload ako je promena u python code-u server se automatski restartuje, i debug console koju flask pokaze ako dodje do errora