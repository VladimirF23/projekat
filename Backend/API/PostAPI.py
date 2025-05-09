from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *
from flask_jwt_extended import jwt_required,get_jwt,get_jwt_identity


post_blueprint = Blueprint('post',__name__,url_prefix='/post')

@post_blueprint.route('/create_post',methods=['POST'])
@jwt_required()
def create_post():
    try:
        user_id = int(get_jwt_identity())  # Uzimam iz tokena id user-a
        data = request.get_json()

        if not data:
            return jsonify({"error":"Invalid JSON format"}),400
        

        required_fields =["title", "content","subreddit_id"]
        missing_fields =[field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error":f"Missing fields: {', '.join(missing_fields)}"}),400

        

        data["created_by"] = user_id
        #da bi napravio post user mora da bude member tog subredit-a

        #prosledjumo post data
        createPostService(data)

        return jsonify({"message": f"User created Post with title: {data['title']},  successfully"}), 201

        
    except IlegalValuesException as e:
        return jsonify({"error":str(e)}), 403

    
    except NotFoundException as e:                              
        return jsonify({"error":str(e)}), 400
        
    except ConnectionException as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500  
