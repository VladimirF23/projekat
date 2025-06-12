#proverava da li se skripta pokrece direktno tj kao main program ili je importovana kao moduo u drugoj skripti
#ako se direktno ranuje onda se ovo dole executuje, app.run pokrece Flask development server i pokrece web app

from extensions import app  # Umesto kreiranja novih objekata, uvozi ih
from Backend.API import *

import threading


from werkzeug.middleware.proxy_fix import ProxyFix

# region ProxyFix,Gunicorn 
# Posto koristim reverse proxy nginx-a moze doci do problema sa prepoznavanjem IP originalnih adresa klienata i originalnog protokola HTTP/HTTPS sa strane python flask aplikacije
# posto ce on videti izvnornu adresu request-a kao IP adresa Nginx-a container-a pa cu koristiti proxy fix, nginx dodaje header-e dodatne za pravi IP usera
# protokol koji se koritsti HTTPS/HTTP, i zato cu koristiti proxyFIx moze se koristiti i u dev-u i u production-u

# Taj IP se koristi za tipa logovanje user-ovih IP-a, da se prikaze user-ov IP, da se vidi da li je HTTP/HTTPS
# A NE KORISTISE  se da Flask salje nazad na taj IP odgovor, nginx uspostavi TCP/IP vezu za Flask-App i onda preko tog socket-a salje request, a Flask-app salje odgovor na taj socket
# nginx isto ima TCP/IP vezu za web browserom klienta pa njemu vraca odgovor isto preko socket-a

#Ako se doda gunicorn onda ce TCP/IP vezu uspostaviti Nginx->Gunicorn a Gunicorn i Flask-app nece imati razlicit tj novu TCP/IP konekciju

# Ovako izgleda slanje requst-ova od user-a ka flask-u (u produkciji isto kao i u dev-u samo mala razlika izmedju gunicorna i flask-a):
# 1.Users Browser (TCP/IP) <--> Nginx: Ostaje isto. Browser se konektuje ka Nginx preko TCP/IP
# 2.Nginx (TCP/IP) <--> Gunicorn: kada Nginx treba  da prosledi API request, establishuje novu TCP/IP connection (ili koristi postojeci iz connection pool-a) ka Gunicorn serveru
# 3.Gunicorn <--> Flask (WSGI): Ovde je Kljucna razlika,  Gunicorn ne koristi zasebanu TCP/IP connection da razgovara sa Flask-om, vec  Gunicorn je WSGI (Web Server Gateway Interface) server
#   - WSGI je Python standard koji definise kako web-server (kao Gunicorn ili Nginx ako je web server) komunicira sa Python web app-om (kao sto je Flask)
#   - Gunicorn load-uje Flask application (main:app) direktno u u svoj process mesto,  kada Gunicorn dobije HTTP request preko svoje TCP/IP connection sa Nginx 
#   - Gunicorn prevodi taj HTTP request u Python WSGI request object u poziva moj Flask application's wsgi_app callable
#   - Komunikacija izmedju Gunicorn i Flask je uglvnm preko local memory poziva ili Unix socket (Ako Gunicorn slusa na Unix socketu za Nginx, to je efikasnije za inter-process komunikaciju na istom hostu)
#     a ne na novoj TCP/IP konekciji
# endregion

# Users Browser (TCP/IP) <--> Nginx <--> Gunicorn <--> Flask (WSGI)


# Primena ProxyFix-a na Flask aplikaciju
# Ovo govori Flasku da veruje X-Forwarded-For i X-Forwarded-Proto headerima od proxyja (Nginx)
# x_for=1     - govori koliko proxy-a ima ispred

#region Opis kako radi x_for

#Scenario 1: Nginx -> Flask

# 1. Client posalje request ka Nginx
# 2. Nginx dobije request, $remote_addr za Nginx je client-ov IP
# 3. proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; govori Nginx da set-uje X-Forwarded-For to client_ip
# 4. Flask dobije:
#    - remote_addr: Nginx-ov internal IP (e.g. 172.17.0.x u Docker-u), ***remote_addr je adresa sa koje se salje ka primaocu***
#    - X-Forwarded-For: client_ip
# 5. Sa ProxyFix(app, x_for=1), Flask ce remove-vati  Nginx IP (iz svog REMOTE_ADDR ne iz X-forwarded-for) i onda koristiti client_ip from X-Forwarded-For
#    rezultat Flask vidi client_ip i ovo je dobro

# Scenario 2: Load Balancer -> Nginx -> Flask

# 1. Client sale request ka Load Balancer-u
# 2. Load Balancer prosledi ka Nginx, LoadBalancer stavi  X-Forwarded-For: client_ip
# 3. Nginx dobije request, $remote_addr za Nginx je Load Balancer-ov IP
# 4. proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for (u config-u); tera Nginx da uzme postojeci X-Forwarded-For (client_ip)
#    i apend-uje svoj $remote_addr (Load Balancer-ov IP)
# 5. Flask dobija:
#    - remote_addr: Nginx's  IP (e.g. 172.17.0.x)
#    - X-Forwarded-For: client_ip, load_balancer_ip
# 6. Sa ProxyFix(app, x_for=2), Flask ce:
#    - Prvo, consider-ovati svoj remote_addr (Nginx's IP) kao immediate untrusted proxy
#    - Onda ce gledati X-Forwarded-For
#      Zbog x_for=2, ce od  X-Forwarded-For: 192.0.0.0 (client_ip), 133.0.0.0 (load_balancer), UZETI client_ip
#      Preostali IP u X-forwarde-For (the original client's IP) ce postati request.remote_addr u Flask-u

# endregion



#x_proto=1 govori Flask-ovom ProxyFix da veruje X-Forwarded-Proto header od samo jednog proxy-ija
#          Nginx postavi X-Forwarded-Proto header to da kaze koji je original scheme (e.g., https or http). 
#          sa x_proto=1 Flask da koristi header od Nginx-a da odredi request.url_scheme (e.g., da li je request bio originalno https:// or http://)
#          i tako osigura url_for generise korektne, sigurne URLs ako treba
# x_host=1    - Veruj X-Forwarded-Host od njednog proxy-ija (Nginx) - Krucijalno za Flask da generise dobre URLs u mojoj aplikaciji, 
#                 pogoto za url_for, osigura da host u generisano URL vidi isto sto i client vidi u svom  browser (e.g. www.yourdomain.com umesto  Nginx IP)


#ne znam da li x_for =0 ili 1 trebalo bi da je 1 
# x_for=1 is correct because you have one trusted proxy (Nginx) that is directly forwarding the request to your Flask application. The X-Forwarded-For header, when it reaches Flask, will contain the original client's IP as its only or last entry if Nginx is configured correctly. ProxyFix then correctly identifies and uses this IP
app.wsgi_app = ProxyFix(app.wsgi_app,x_for=1, x_proto=1,x_host=1)




#Nema potreba da API nesto menjam on ce return-ovati npr postov-e i code 200, znace na koju IP Adresu posto kada se uspostavi konekcija client-server , hTTP se oslanja na TCP/IP protokol
# i flask odgovara 



#NE ZABORAVI DA REGISTUJES BLUEPRINTOVE !
app.register_blueprint(registration_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(subbredit_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(post_blueprint)
app.register_blueprint(search_blueprint)



if __name__ =='__main__':
    #thread pre app startujem da ne bi doslo do ne pokretanja thread-a
    cacheThread = threading.Thread(target=UpdatePopularSubreddits_cache_Service, daemon=True)
    cacheThread.start()

    #app.run je za development za production cu koristiti Gunicorn
    app.run(host='0.0.0.0', port=5000,debug=True, threaded=True)#debug ->autoReload ako je promena u python code-u server se automatski restartuje, i debug console koju flask pokaze ako dodje do errora

    #za refresh kesiranja useranema i subreddita i njihovih id-a
