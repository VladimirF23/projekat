from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt
from datetime import timedelta,datetime
#metoda je post jer POST drzi sensitive data (email/password) u request body a on nije logovan u browser history
#Get exposuje parametre u URL sto nije sigurno
registration_blueprint = Blueprint('registration',__name__,url_prefix='/registration')

@registration_blueprint.route('', methods =['POST'])
def register_user():
    try:
        user_data =request.get_json()
        #username,email,password
        if not user_data:
            return jsonify({"error":"Invalid JSON format"}),400
        

        #pitaj chat gpt da li je moguce posto ovde imamo proveru, da nekako user pogodi one metode u Engine layeru i onda da zato moramo da imamo provere na vise layer-a
        required_fields =["username", "email", "password"]
        missing_fields =[field for field in required_fields if field not in user_data]

        if missing_fields:
            return jsonify({"error":f"Missing fields: {', '.join(missing_fields)}"}),400

        #service layer zovemo
        RegisterUserService(user_data)

        #Posto je potrebn da takodje kreiramo JWT token prilikom registracije a ja sam se ogranicio da se unutar MysqlDB generise id user-a 
        #necemo moci da uzmemo id bez da se loginujemo pa cu samo iskoristiti funkciju iz logina i logiku iz logina

        #mysql ce vratiti dict posto sam stavio da kod cursora dict=True
        user =  LoginUserService(user_data)

        access_token =create_access_token(identity=str(user["id"]),additional_claims={"global_admin":"global_admin" if user["global_admin"] else "user"},expires_delta=timedelta(minutes=15))              #najboljeje id da koristimo za identity jer se on niakd nece menjatim, 
        refresh_token = create_refresh_token(identity=str(user["id"]),additional_claims={"global_admin":"global_admin" if user["global_admin"] else "user"},expires_delta=timedelta(days=7))              #a username se moze menjati


        redis_client.set(f"access_token:{access_token}","valid",ex=int(timedelta(minutes=15).total_seconds()))  #radis ex uzimamo int u total sekundama !
        redis_client.set(f"refresh_token:{refresh_token}","valid",ex=int(timedelta(days=7).total_seconds()))

        return jsonify({"message": "User registered successfully", "access_token": access_token, "refresh_token": refresh_token}), 201


    except IlegalValuesException  as e:
        return jsonify({"error":str(e)}), 400
    
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}),500
    









