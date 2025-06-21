from ..Engine import *
from flask import Blueprint, request,jsonify,make_response
from ..CustomException import *
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt,set_access_cookies,set_refresh_cookies,get_csrf_token,get_jwt_identity,decode_token,unset_jwt_cookies,verify_jwt_in_request
from datetime import timedelta,datetime
#iz maina importujemo objekat jwt koji smo kreirali


from extensions import jwt,redis_client   
import redis


#Check Redis connection on app startup
try:
    redis_client.ping()  # Test Redis connection
except redis.ConnectionError:
    raise Exception("Failed to connect to Redis.")

auth_blueprint  = Blueprint("auth",__name__,url_prefix="/auth")

@auth_blueprint.route('/login',methods=['POST'])
# metoda je post jer POST drzi sensitive data (email/password) u request body a on nije logovan u browser history #Get exposuje parametre u URL sto nije sigurno
# primaran posao logina kada koristimo HttpOnlyCookie je da setuje accsess i refresh tokene kao Cooki-e koje JS ne moze da pristupi
# i vraca se poruka Uspesan login ali se ne vraca JWT ili user data Browser ce dobiti Set-Cookie headers i automatski store-vati HttpOnly cookie i JS citljiv CSRF cookie
# Front end ne moze da procita JWT cookie zato sto su HttpOnly i ne moze da vidi info o user-u (username,id,global_admin)
# Odma nakon uspesnog logina na frontu se salje request na API da se za sada loginovanog user-a posalje info da bi React mogao to da prikazuje na UI-u
def login():
    try:
        user_data = request.get_json()
        if not user_data:
            return jsonify({"error":"Invalid JSON format"}),400
        
        required_fields =["username", "password"]
        missing_fields =[field for field in required_fields if field not in user_data]

        if missing_fields:
            return jsonify({"error":f"Missing fields: {', '.join(missing_fields)}"}),400
        
        #mysql ce vratiti dict posto sam stavio da kod cursora dict=True
        user =  LoginUserService(user_data)

        #na globalnom nivou u main-u smo set-upovali token i koje algoritam sa enkripciju da koristi i sve, ovde kreiramo te tokene
        #identinty mora biti str() 
        access_token =create_access_token(identity=str(user["id"]),additional_claims={"global_admin":"global_admin" if user["global_admin"] else "user"},expires_delta=timedelta(seconds=20))              #najboljeje id da koristimo za identity jer se on niakd nece menjatim, 
        refresh_token = create_refresh_token(identity=str(user["id"]),additional_claims={"global_admin":"global_admin" if user["global_admin"] else "user"},expires_delta=timedelta(days=7))              #a username se moze menjati

        #JWT_COOKIE_SECURE = True -> kaze Flask-JWT-Extended da JWT cookie  salje SAMO preko HTTPS (secure connection), da ne bi preko HTTP i tako sprecava man i middle attack
        #JWT_COOKIE_CSRF_PROTECT = True -> drugi CSRF token se pravi (random string razlicit od JWT tokena) i on se MORA slati u custom header-u (X-CSRF token)
        # sa svakim state changing reqeustom POST,PUT,DELETE etc, AKO CSRF token u headeru ne matchuje ona u cookie-u request se odbija

        # OVO JE BITNO JER:
        #jer cak i sa HttpOnly, moj browser ce automatski attach cookies na requests — ukljucijuci i one triggere-ovane od attacker (preko malicious <form> ili <script>).
        #CSRF protection zaustavlja ne-authorizovane komande da budu izvrsene SA strane user-a samo zato sto njegov browser auto-attachuje cookie-je.



        #Cuvacu u reddisu ali sa metadatom i JTI kao kljucem da bih mogao lakse u refresh-u 
        #redis_client.set(f"access_token:{access_token}","valid",ex=int(timedelta(minutes=15).total_seconds()))  #radis ex uzimamo int u total sekundama !
        #redis_client.set(f"refresh_token:{refresh_token}","valid",ex=int(timedelta(days=7).total_seconds()))

        decoded_access  = decode_token(access_token)
        decoded_refresh = decode_token(refresh_token)

        access_jti  = decoded_access["jti"]
        refresh_jti = decoded_refresh["jti"]

        user_metadata_access = {
                "user_id": user["id"],
                "username": user["username"],
                "global_admin": user["global_admin"],
                "status": "valid",
                "issued_at": decoded_access["iat"],  # epoch
                "expires": decoded_access["exp"],     # epoch
                "type" : "access_token"

        }
        user_metadata_refresh = {
                "user_id": user["id"],
                "username": user["username"],
                "global_admin": user["global_admin"],
                "status": "valid",                    #necu menjati ovo samo cu blacklistovati token...
                "issued_at": decoded_refresh["iat"],  # epoch
                "expires": decoded_refresh["exp"],     # epoch
                "type" : "refresh_token"

        }

        #storujemo u reddisu i JTI je kljuc to nam je bolje nego da stavljamo ceo JWT u reddis zato sto preko JTI lako nadjemo tokene po user-u, Revocation support imamo
        # user moze da ima vise sesija pa cemo storovati na osnovu userID u setu sve JTI keyeve tog usera to nam omogucava lako da :
        #   sve tokene usera obrisemo, invalidaciju specificne sesije bez efekte na druge
        #   npr Admin disables user-ov account -> fetchujem sve jti iz user_tokens:{userId} i obrise ih sve
        #   npr User se odjavi server obrise taj jti i removuje jti iz user_tokens:{userId}
        #   user_tokens:{userId} => set of {jti1, jti2, jti3, ...}
        

        #Redis Pipeline Pipelines dozvoljavaju slanje vise komandi ka Redisu odjednom — 
        #poboljsava performance tako sto smanjujemo round trips — ALI pipeline nema garancije atomicnosti  (ako ne pozovemo multi() unutar pipeline-a).
        # "atomic operation means that the entire operation is done as a single indivisible step" -> u principu kao transakcija ili se svi komande se izvrse ili ni jedna !
        
        #da bih osigurao da se dese sva pistanja u razlicite set-ove 

        pipe = redis_client.pipeline()

        #queu-jem komande na pipe i na execute-u se sve izvrse i tako izbegnem da se delimicno izvrse
        pipe.setex(f"access_token:{access_jti}",int(timedelta(minutes=15).total_seconds()),json.dumps(user_metadata_access))    #svaki individualno
        pipe.setex(f"refresh_token:{refresh_jti}",int(timedelta(days=7).total_seconds()),json.dumps(user_metadata_refresh))

        #dodajemo sve id tokena koji pripadaju user-u, ukljucujuci i refresh token
        pipe.sadd(f"user_tokens:{user['id']}", access_jti, refresh_jti)

        pipe.execute()

        #npr alice je logovan-a sa 2 razlicita device-a (ili sesije) svaka sesija dobija access token i refresh token, (nisam refresh napisao)
        #  Redis Key	                  Stored Value (simplified JSON)	                                     TTL
        #access_token:abc123	{ "user_id": "1", "username": "alice", "type": "access_token", ... }	      15 minutes
        #access_token:ghi789	{ "user_id": "1", "username": "alice", "type": "access_token", ... }          15 minutes

        #set za svakog user-a da mogu da trackujem njihove aktivne tokene
        #   set       user_id
        # user_tokens:  1       {abc123, ghi789}


        response = make_response(jsonify({"message": "User logged in successfully"}))

        #setujemo access and refresh cookies HTTP only su zbog XSS
        #JWT token stavljam unutar cookie-a, JWT token se prenosi preko cooki-a i u config-u sam stavio JWT_COOKIE_SECURE =True tj da se koristi HTTPS
        #i onda HTTPOnly cookies nisu pristupacni JavaScriptu i to stiti JWT token od toga da bude ukraden u XSS napadu
        #HTTP nije enkriptovan pa svakom na networku npt (WIfi-u) moze da cita i modifikuje traffic ukljucujuci i nas JWT token, login info, i user data
        #HTTPS enkriptuje komunikaciju izmedju browsera i servera
        set_access_cookies(response,access_token)
        set_refresh_cookies(response,refresh_token)
        #HttpOnly is a cookie attribute that prevents JavaScript from accessing the cookie using document.cookie.

        # NE TREBA OVO zato sto set_access_cookies automatski pravi csrf_access_cookie u jwt configu samo cu namestiti da mu ime bude csrf_cookie
        # posto mi u frontu ga tako cita
        
        # Uzmemo is accses_token-a (JWT) zaseban CSRF token cookie (JS citljiv), CSRF token se GENERISAO VEC zasebno u JWT tokenu jer smo stavili JWT_COOKIE_CSRF_PROTECT = True
        # csrf_token = get_csrf_token(access_token)

        # response.set_cookie(
        #     "csrf_token",
        #     csrf_token,
        #     httponly=False,       #Da bi java script mogla da procita csrf token
        #     secure=True,
        #     samesite="Lax",     #proveri Lax jos
        #     max_age=15 *60    #15 min
        # )

        #login vraca Cookie i CSRF i JS nece moci da 
        return response,201

    except NotFoundException as e:                              #ako je neuspesan login desice se exception, DB sloj dize taj exception
        return jsonify({"error":str(e)}), 400
    except redis.RedisError as e:
        return jsonify({"error":"Redis error","details":str(e)}),500
    except ConnectionException as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500   


#kada Flask-JWT-extended vidi @jwt.token_in_blocklist_loader on registruje check_if_token_is_blacklisted funkciju na svaki pristuzajuci JWT
#Svaki put kada se pristupa @jwt_required() Flask-JWT-Extended extrakctuje JWT iz requesta (iz authorizathion header-a) i provera JWT potpis i istek 
#Ako je validan TEK onda zove check_if_token...
#Redis get kao da smo prosledili hashmapi kljuc i proveravamo da li je taj TOKEN idalje validan
@jwt.token_in_blocklist_loader
def check_if_token_is_blacklisted(jwt_header, jwt_payload):     #jwt_header sadrzi metadatu od  tokena, algoritam i type, payload sadrzi decodiran body  JWT sa identitetom i CUSTOM CLAIM-ovima
    jti = jwt_payload["jti"]                                    #jti unique id koji se dodeljuje svakom tokenu prilikom kreatije NIJE isto sto i customClaim
    return redis_client.get(f"blocked_token:{jti}") =="invalid"   #reddis dekodira odma u string jer sam tako stavio u redis clientu
#True -> invalid tj nije vise validan token
#Znaci FLASK-JWT-Extended dekodira token
#Proveri signature i expiration
#pozove check_if_token_is_blacklisted
#Ako funkcija vrati TRUE znaci da je blaclistovan token i request se rejectuje sa 401 Unauthorized, ako vrati False dozvoljava se pristup 200 ok




#u TODO OVO SE MORA POVEZATI SA FRONT-om KOJI CE SLATI ZAHTEV ZA REFRESH-OM KAD DETEKTUJE DA ISTICE VREME ACCESS TOKENA DA SE USER NE BI LOGOUT-OVAO
@auth_blueprint.route('/refresh',methods=['POST'])
@jwt_required(refresh=True)             #zahteva validan REFRESH token da bi se pristupilo ovoj funkciji
def refresh():
    try:
        #identity = get_jwt()["sub"]    isto je sto i ovo dole

        #uzima od refresh jwt-a INFO, zato sto samo cookie sa refresh tokenom moze da pristupi ovoj funkciji zbog refresh=True
        #ne moram da unpackujem jwt token in cooki-a to se automatski uradi sa get_jtw_identity

        identity = get_jwt_identity()   # id user-a
        claims = get_jwt()              # ceo JWT REFRESH TOKEN-a payload ukljucujuci "jti", "exp", "global_admin", etc.

        #potrebno je u reddisu invalidatovati stari token i dodati ovaj novi
        old_refresh_jti  = claims.get("jti")         #unique token id za revocation je koristan

        #Blacklistujemo stari refresh i stari access token, i radimo refresh token rotation tj izdajemo novi refresh token

        #"In JWT-based authentication, tokens are self-contained — meaning they don’t require server-side sessions to validate them. But this also means:
        #   If a token hasn’t expired, it’s technically still valid even if the user logs out or it’s supposed to be blocked — unless you track and reject it manually".
        
        pipe = redis_client.pipeline()

        old_access_token = request.cookies.get("access_token_cookie")  #Blacklistujemo stari ACCESS token kog vadimo iz cookie-a, default ime
        if old_access_token:                                            
            try:
                decoded_old_access = decode_token(old_access_token)    #decode_token ce biti dovoljno siguran zato sto se prenosi preko HTTP samo i CSFR secure je
                old_access_jti = decoded_old_access["jti"]

                pipe.setex(f"blocked_token:{old_access_jti}",int(timedelta(minutes=30).total_seconds()),"invalid"
                )
            except Exception as err:
                print(f"Old access token decode failed: {err}")
                pass  # Istekli or malformed token – ignorisemo

         # Blacklistujemo the old refresh token (optional but safer for rotation)
        pipe.setex(f"blocked_token:{old_refresh_jti}",int(timedelta(days=7).total_seconds()),"invalid")       
        
        
        # pravimo novi acsess token
        new_access_token = create_access_token(identity=identity,additional_claims={"global_admin": claims.get("global_admin")},expires_delta=timedelta(minutes=15))

        #novi refresh token pravimo
        new_refresh_token = create_refresh_token(identity=identity,additional_claims={"global_admin": claims.get("global_admin")},expires_delta=timedelta(days=7))


        decoded_new_access  = decode_token(new_access_token)
        decoded_new_refresh = decode_token(new_refresh_token)

        new_jti_access = decoded_new_access["jti"]
        new_jti_refresh = decoded_new_refresh["jti"]

        # Metadata user-a
        user_metadata_access = {
            "user_id": identity,
            "username": claims.get("username", ""),  # optional: fetch again if needed
            "global_admin": claims.get("global_admin"),
            "status": "valid",
            "issued_at": decoded_new_access["iat"],
            "expires": decoded_new_access["exp"]
        }

        user_metadata_refresh = {
            "user_id": identity,
            "username": claims.get("username", ""),  # optional: fetch again if needed
            "global_admin": claims.get("global_admin"),
            "status": "valid",
            "issued_at": decoded_new_refresh["iat"],
            "expires": decoded_new_refresh["exp"]
        }

        # Store new access token by JTI
        pipe.setex(f"access_token:{new_jti_access}",int(timedelta(minutes=15).total_seconds()),json.dumps(user_metadata_access))
        pipe.setex(f"refresh_token:{new_jti_refresh}",int(timedelta(days=7).total_seconds()),json.dumps(user_metadata_refresh))
    

        # dodajemo u set id usera njegov jti
        pipe.sadd(f"user_tokens:{identity}", new_jti_access, new_jti_refresh)


        #executujemo sve reddis komande atomicno 
        pipe.execute()

        #novi accses stavljamo u secure cookie
        response = make_response(jsonify({"message": "Access token refreshed"}))
        set_access_cookies(response, new_access_token)
        set_refresh_cookies(response,new_refresh_token)


        # Ne treba ovo dole set_access_cookies ce automatski postaviti csrf_access_token
        # Regenerisemo i setujemo new CSRF token iz new_access tokena
        # csrf_token = get_csrf_token(new_access_token)

        # response.set_cookie(
        #     "csrf_token",
        #     csrf_token,
        #     httponly=False,     #da moze JS da pristupi csrf
        #     secure=True,
        #     samesite="Lax",
        #     max_age=15 * 60
        # )        
        
        return response
    
    #mora pre genericno exception-a ovaj redis exception
    except redis.RedisError as e:
        return jsonify({"error":"Redis error","details":str(e)}),500
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# {
#   "sub": 123,                                       custom claim, tj id usera u DB 
#   "exp": 1700000000,                                preostalo vreme
#   "jti": "abcd-1234-efgh-5678"                      jedisntven id koji se dodeljuje svakom tokenu pri kreaciji
# }

#logout_blueprint = Blueprint("logout",__name__,url_prefix="/logout") Ne treba logout blueprint posto grupisemo srodne  route unutar istog Blueprinta
#zbog bolje modularnosti i organizovanosti, za logout POST /auth/logout
                                 
@auth_blueprint.route('/logout',methods=['POST'])
@jwt_required()                              #provera da li je jwt token prisutan u headeru/cookiju,proverava potpis i da li je nesto radjeno sa njim, i provera da nije istekao token
def logout():                               #takoddje raiseuje error ako nema tokena,token je invalid,expired ili revokovan
    try:
        jti= get_jwt()["jti"]
        exp = get_jwt()["exp"]  # da dinamicki postavimo kolko ce u redisu (blacklist) biti token nako sto se logoutuje, postavimo da je timeout trenutno kolko mu je ostalo od original.
        identity = get_jwt_identity()   #vraca id u string formatu

        #VAZNO je namestimo ttl za blacklist da se ne bi desilo da blacklist istekne a token TTL nastavi da postoji onda je presta da bude blacklistovan ! 

        if not jti or not exp:
            return jsonify({"error":"Invalid JWT structure"}),400

        ttl = int(exp - datetime.utcnow().timestamp())
        if ttl < 0:
            ttl=1       #zbog clock skew, imamo sat na serveru i JWT validatora ako slucajn sad kod JWT kasni za 5 sekundi, ako dobijemo negativan ttl da ne bude error u redisu

        pipe = redis_client.pipeline()
        pipe.multi()

        #pri logout-u usera blaclistujemo njegov accsess token i refresh token, bolje je blacklistovanj-e nego da ih brisem u access_token i refresh_token  reddis-u
        # jer bi bilo onda inconsistency ako konkrutetno app pokusa da refresh-uje i validatuje tokene, JWT_required ce izbeci race conditione jel prvo provera blacklist pa tek dozvoljava funk da se izvrsi


        pipe.setex(f"blocked_token:{jti}", ttl, "invalid")      #dodamo expiration
 
        #iz seta aktivnih access tokena brisemo acsess tokena od trenutne sesije user-a koja se odjavljuje
        pipe.srem(f"user_tokens:{identity}", jti)

        #blacklistovanje REFRESH tokena


        # Uzmemo refresh token iz cookie-a, ovo je bio prethodni problem sa logout-om jer sam preko ovog verift_jwt_in_request...
        # ali ga necu verifikovati preko verify_jwt_in_request(refresh=True)
        # jer @jwt_required() iznad vec brine o autenticnosti
        # Njegova validacija ce se desiti u okviru pipe.setex ako je prisutan
        refresh_token_cookie_value = request.cookies.get('refresh_token_cookie')

        if refresh_token_cookie_value: # provera da li postoji uopste refresh_token
            try:
                # Dekodiramo refresh token (Flask-JWT-Extended ovo radi sigurno proverava potpis)
                # Nema potrebe za 'verify_jwt_in_request' ovde jer je cilj samo blacklistovanje
                # a ne autorizacija pristupa ruti
                decoded_refresh = decode_token(refresh_token_cookie_value)
                refresh_jti = decoded_refresh["jti"]
                refresh_exp = decoded_refresh["exp"]

                ttl_refresh = int(refresh_exp - datetime.utcnow().timestamp())
                if ttl_refresh < 0:
                    ttl_refresh = 1 # Minimalni TTL

                pipe.setex(f"blocked_token:{refresh_jti}", ttl_refresh, "invalid")
                pipe.srem(f"user_tokens:{identity}", refresh_jti) # Ukloni JTI refresh tokena iz seta korisnika
            except Exception as e:
                # Loguj grešku ako dekodiranje refresh tokena ne uspe (npr. istekao je ranije, tampered)
                print(f"Error decoding or blacklisting refresh token during logout: {e}")
                # Nastavi dalje, jer je glavni cilj logouta postignut (access token je blacklistovan)




        #izvrsavamo reddis komande atomicno
        pipe.execute()      


        response = make_response(jsonify({"message": "Logged out successfully"}), 200)
        unset_jwt_cookies(response)  #OVO JE NAJBITNIJE 
                                     #Ovo šalje instrukcije browser-u da obriše
                                     # HttpOnly kolačiće (access_token_cookie, refresh_token_cookie, csrf_access_token, csrf_refresh_token)

        # brisemo i refresh zato sto: Ostavljanje refresh cookie znaci da client moze da zatrazi novi acces cookie token silently preko POST /refresh
        # ako se ne obrise onda: client moze da refresh-uje silently, sto onda ponistava logging out

        #Ovo je kad admin banuje user-a ili sa LOGOUT out of everything
        # for jti in redis_client.smembers(f"user_tokens:{identity}"):
        #    redis_client.setex(f"blocked_token:{jti.decode()}", 7 * 24 * 3600, "invalid")  # 7 days
        #redis_client.delete(f"user_tokens:{identity}")


        return response
    
    except redis.RedisError as e:
        return jsonify({"error":"Redis error","details":str(e)}),500
    except Exception as e:
        return jsonify({"error":str(e)}), 500





@auth_blueprint.route('/admin', methods=['GET'])
@jwt_required()
def admin_only():
    try:
        jwt_data = get_jwt()
        if jwt_data.get("global_admin").lower() != "global_admin":             #u tokenu sam dodao addtion_claim field u jwt tokenu za global admin-a
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify({"message": "Welcome, Admin!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#ADMIN FUNCTION TO BAN USER TODO
#Concurrency safety:

#logout all Since you’re tracking per-user sets, you may eventually want to wrap any mass revocation logic (e.g. logout-all) in a transaction too.



#Ovo se automatski poziva nakon uspesnog logina sa strane front-a i ovako osiguravam da login imao single responsability a to je set-ovanje access/refresh/csrf tokena
#pogledaj u notepadu sam objasnio zasto ovako 
@auth_blueprint.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_details():
    try:
        #current_user_id = get_jwt_identity() 
        claims = get_jwt()                          # Get all claims from the access token

        
        # Meta data za access tokene se cuva u Redisu
        # Uzecemo tu metadatu iz redis-a da bi imali sveze podatke 
        # ***Ovako izbegavamo da zovemo MySQL DB za podatke svakog usera*** 
        access_jti = claims.get("jti")
        user_metadata_str = redis_client.get(f"access_token:{access_jti}")

        if not user_metadata_str:
            # Ovaj slucaj se nece desiti ako token validan i nije  blacklistovan
            # Ali za saki slucaj ako je revokovan ili istekao iz Redis-a
            # A JWT-Extended nekako uspeo da ga validira (nvrjm da ce se desiti)
            return jsonify({"error": "User data not found in Redis or session invalid"}), 404

        user_metadata = json.loads(user_metadata_str)

        # Uzmemo podatke iz acces token-a
        user_details = {
            "id": user_metadata.get("user_id"),
            "username": user_metadata.get("username"),
            "global_admin": user_metadata.get("global_admin") == "global_admin" #pazi u string ga convertujem ovde ! 
        }

        return jsonify(user_details), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve user details", "details": str(e)}), 500
