from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *
from flask_jwt_extended import JWTManager,create_access_token,create_refresh_token,jwt_required,get_jwt
from datetime import timedelta,datetime
import redis
auth_blueprint  = Blueprint("auth",__name__,url_prefix="/auth")

# Redis Client Setup 
redis_client = redis.StrictRedis.from_url("redis://localhost:6379/0", decode_responses=True)

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


        redis_client.set(f"access_token:{access_token}","valid",ex=timedelta(minutes=15))
        redis_client.set(f"refresh_token:{refresh_token}","valid",ex=timedelta(days=7))

        return jsonify({"access_token": access_token, "refresh_token":refresh_token})

    except NotFoundException as e:                              #ako je neuspesan login desice se exception, DB sloj dize taj exception
        return jsonify({"error":str(e)}), 400
        
    except ConnectionException as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500   
    

# {
#   "sub": 123,                                       ovo je id
#   "exp": 1700000000,                                preostalo vreme
#   "jti": "abcd-1234-efgh-5678"
# }

#logout_blueprint = Blueprint("logout",__name__,url_prefix="/logout") Ne treba logout blueprint posto grupisemo srodne  route unutar istog Blueprinta
#zbog bolje modularnosti i organizovanosti, za logout POST /auth/logout
                                 
@auth_blueprint.route('/logout',methods=['POST'])
@jwt_required()                                 #provera da li je jwt token prisutan u headeru/cookiju,proverava potpis i da li je nesto radjeno sa njim, i provera da nije istekao token
def logout():                               #takoddje raiseuje error ako nema tokena,token je invalid,expired ili revokovan
    try:
        #uzmemo trenutni jti
        jti= get_jwt()["jti"]
        exp = get_jwt()["exp"]  # da dinamicki postavimo kolko ce u radisu (blocklisti) biti token nako sto se logoutuje
        ttl = int(exp - datetime.utcnow().timestamp())

        #pri logoutu moramo user-a invalidatovati njegov token tako sto ga dodamo na blacklistu
        redis_client.set(f"blocket_token:{jti}","invalid",ex=int(ttl))                    
        #i ovde dodajemo expiration time da nam ne bi za dzabe zauzimamo memoriju, posto se RADIS je inmemory database i sve se cuva u RAM-u 
        #pa nema potrebe cuvari blacklistovane tokene neograniceno jer ce zauzeti svu memoriju
        #Avoidujemo memory leaks


        return jsonify({"message":"Logged out successfully"}),200
    except Exception as e:
        return jsonify({"error":str(e)}), 500


@auth_blueprint.route('/admin', methods=['GET'])
@jwt_required()
def admin_only():
    try:
        jwt_data = get_jwt()
        if jwt_data.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify({"message": "Welcome, Admin!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
