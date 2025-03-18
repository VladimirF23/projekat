from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *

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
        return jsonify({"message":"User registered successfully"}),201
    
    except IlegalValuesException  as e:
        return jsonify({"error":str(e)}), 400
    
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}),500
    









