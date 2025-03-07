
from ..Engine import *

from flask import Blueprint, request,jsonify
from ..CustomException import *


registration_blueprint = Blueprint('registration',__name__,url_prefix='/registration')

@registration_blueprint.route('', methods =['POST'])
def register_user():
    try:
        user_data =request.get_json()

        if not user_data:
            return jsonify({"error":"Invalid JSON format"}),400
        

        #service layer zovemo
        RegisterUserService(user_data)
        return jsonify({"message":"User registered successfully"}),201
    
    except IlegalValuesException  as e:
        return jsonify({"error":str(e)}), 400
    
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}),500
    









