from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *
from flask_jwt_extended import jwt_required,get_jwt,get_jwt_identity


subbredit_blueprint = Blueprint('subbredit_creation',__name__,url_prefix='/subreddit')

#samo admin moze da napravi subbredit
@subbredit_blueprint.route('/create_subbredit',methods=['POST'])
@jwt_required()                                                                 #blacklist za proveru tokena je definisan u authentification pa ce se automatski i ovde proverati kada se pozove jwt_required
def create_subreddit():
    claims = get_jwt()
    if claims.get("global_admin") != "global_admin":
        return {"msg": "Admins only!"}, 403

    #int id
    created_by = int(get_jwt_identity())  # Uzimam iz tokena id usera koji pokusava da napravi subbredit zato sto mi treba bolje created_by u subrreditu

    try:
        subbredit_data = request.get_json()
        required_fields =["name", "description"]

        missing_fields =[field for field in required_fields if field not in subbredit_data]

        if missing_fields:
            return jsonify({"error":f"Missing fields: {', '.join(missing_fields)}"}),400

        subbredit_data["created_by"] = created_by

        #prosledjujemo service layeru
        CreateSubbredit(subbredit_data)

        return jsonify({"message":"Subbredit created successfully"}),201
       
    
    except IlegalValuesException  as e:
        return jsonify({"error":str(e)}), 400
    
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}),500
