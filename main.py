#proverava da li se skripta pokrece direktno tj kao main program ili je importovana kao moduo u drugoj skripti
#ako se direktno ranuje onda se ovo dole executuje, app.run pokrece Flask development server i pokrece web app

from extensions import app  # Umesto kreiranja novih objekata, uvozi ih
from Backend.API import *

import threading

#NE ZABORAVI DA REGISTUJES BLUEPRINTOVE !
app.register_blueprint(registration_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(subbredit_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(post_blueprint)
app.register_blueprint(search_blueprint)



if __name__ =='__main__':
    app.run(host='0.0.0.0', port=5000,debug=True, threaded=True)#debug ->autoReload ako je promena u python code-u server se automatski restartuje, i debug console koju flask pokaze ako dodje do errora

    #za refresh kesiranja useranema i subreddita i njihovih id-a
    thread = threading.Thread(target=UpdatePopularSubreddits_cache_Service, daemon=True)
    thread.start()