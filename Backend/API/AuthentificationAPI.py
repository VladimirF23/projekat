from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt
from datetime import timedelta,datetime
#iz maina importujemo objekat jwt koji smo kreirali


from extensions import jwt,redis_client   # OVO POPRAVI NE RADI ONAJ check
import redis

auth_blueprint  = Blueprint("auth",__name__,url_prefix="/auth")

#Check Redis connection on app startup
try:
    redis_client.ping()  # Test Redis connection
except redis.ConnectionError:
    raise Exception("Failed to connect to Redis.")

@auth_blueprint.route('/login',methods=['POST'])
#metoda je post jer POST drzi sensitive data (email/password) u request body a on nije logovan u browser history
#Get exposuje parametre u URL sto nije sigurno
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
        access_token =create_access_token(identity=user["id"],additional_claims={"role":user["role"]},expires_delta=timedelta(minutes=15))              #najboljeje id da koristimo za identity jer se on niakd nece menjatim, 
        refresh_token = create_refresh_token(identity=user["id"],additional_claims={"role":user["role"]} ,expires_delta=timedelta(days=7))              #a username se moze menjati


        redis_client.set(f"access_token:{access_token}","valid",ex=int(timedelta(minutes=15).total_seconds()))  #radis ex uzimamo int u total sekundama !
        redis_client.set(f"refresh_token:{refresh_token}","valid",ex=int(timedelta(days=7).total_seconds()))

        return jsonify({"access_token": access_token, "refresh_token":refresh_token})

    except NotFoundException as e:                              #ako je neuspesan login desice se exception, DB sloj dize taj exception
        return jsonify({"error":str(e)}), 400
        
    except ConnectionException as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500   

#kada Flask-JWT-extended vidi @jwt.token_in_blocklist_loader on registruje check_if_token_is_blacklisted funkciju na svaki pristuzajuci JWT
#Svaki put kada se pristupa @jwt_required() Flask-JWT-Extended extrakctuje JWT iz requesta (iz authorizathion header-a) i provera JWT potpis i istek 

#Ako je validan TEK onda zove check_if_token...
#Redis get kao da smo prosledili hashmapi kljuc i proveravamo da li je taj TOKEN idalje validan
@jwt.token_in_blocklist_loader
def check_if_token_is_blacklisted(jwt_header, jwt_payload):     #jwt_header sadrzi metadatu od  tokena, algoritam i type, payload sadrzi decodiran body  JWT sa identitetom i CUSTOM CLAIM-ovima
    jti = jwt_payload["jti"]                                    #jti unique id koji se dodeljuje svakom tokenu prilikom kreatije NIJE isto sto i customClaim
    return redis_client.get(f"blocked_token:{jti}") =="invalid" 
#True -> invalid tj nije vise validan token
#Znaci FLASK-JWT-Extended dekodira token
#Proveri signature i expiration
#pozove check_if_token_is_blacklisted
#Ako funkcija vrati TRUE znaci da je blaclistovan token i request se rejectuje sa 401 Unauthorized, ako vrati False dozvoljava se pristup 200 ok

#u TODO je dodato kako ovo radi silent sa JAVASCRIPTOM
@auth_blueprint.route('/refresh',methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        identity = get_jwt()["sub"]
        new_access_token = create_access_token(identity=identity, expires_delta=timedelta(minutes=15))

        #potrebno je u reddisu invalidatovati stari token i dodati ovaj novi
        old_jti = get_jwt()["jti"]  
        #redis_client.set(f"blocked_token:{old_jti}", "invalid", ex=int(timedelta(minutes=15).total_seconds()))  # Expiry should be same as new access token

        #novi token
        #redis_client.set(f"access_token:{new_access_token}", "valid", ex=int(timedelta(minutes=15).total_seconds()))  # Set expiration time

        #opcijonalno updejtovati refresh token ali nema potrebe posto oni dugu traju, pa je fokus na access tokene
        return jsonify({"access token":new_access_token})

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
@jwt_required()                                 #provera da li je jwt token prisutan u headeru/cookiju,proverava potpis i da li je nesto radjeno sa njim, i provera da nije istekao token
def logout():                               #takoddje raiseuje error ako nema tokena,token je invalid,expired ili revokovan
    try:
        #uzmemo trenutni jti
        jti= get_jwt()["jti"]
        exp = get_jwt()["exp"]  # da dinamicki postavimo kolko ce u radisu (blocklisti) biti token nako sto se logoutuje, postavimo da je timeout trenutno kolko mu je ostalo od original.
        
        if not jti or not exp:
            return jsonify({"error","Invalid JWT structure"}),400

        ttl = int(exp - datetime.utcnow().timestamp())

        #pri logoutu moramo user-a invalidatovati njegov token tako sto ga dodamo na blacklistu
        redis_client.set(f"blocked_token:{jti}","invalid",ex=int(ttl))                    
        #i ovde dodajemo expiration time da nam ne bi za dzabe zauzimamo memoriju, posto se RADIS je inmemory database i sve se cuva u RAM-u 
        #pa nema potrebe cuvari blacklistovane tokene neograniceno jer ce zauzeti svu memoriju
        #Avoidujemo memory leaks


        return jsonify({"message":"Logged out successfully"}),200
    
    except redis.RedisError as e:
        return jsonify({"error":"Redis error","details":str(e)}),500
    except Exception as e:
        return jsonify({"error":str(e)}), 500




@auth_blueprint.route('/admin', methods=['GET'])
@jwt_required()
def admin_only():
    try:
        jwt_data = get_jwt()
        if jwt_data.get("role").lower() != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify({"message": "Welcome, Admin!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

