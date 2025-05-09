from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *
from flask_jwt_extended import jwt_required,get_jwt,get_jwt_identity




user_blueprint = Blueprint('user', __name__, url_prefix='/user')



@user_blueprint.route('/join_subreddit',methods=['POST'])
@jwt_required()
def joinSubreddit():
    try:
        user_id = int(get_jwt_identity())  # Uzimam iz tokena id 
        data = request.get_json()
        subreddit_id = data.get("subreddit_id")

        if not subreddit_id:
            return jsonify({"error": "Missing subreddit_id"}), 400
        
        #service
        joinSubredditService(user_id,subreddit_id)

        return jsonify({"message": "Joined subreddit successfully"}), 200

    except IlegalValuesException as e:
        return jsonify({"error":str(e)}), 400

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}),500

@user_blueprint.route('/leave_subreddit',methods=['POST'])
@jwt_required()
def leaveSubreddit():
    try:
        user_id = int(get_jwt_identity())  # Uzimam iz tokena id 
        data = request.get_json()
        subreddit_id = data.get("subreddit_id")         #preko react-a cu namestiti da svako dugme je poveazano sa id subreddita

        if not subreddit_id:
            return jsonify({"error": "Missing subreddit_id"}), 400
        
        #service
        leaveSubredditService(user_id,subreddit_id)

        return jsonify({"message": "Left subreddit successfully"}), 200

    except IlegalValuesException as e:
        return jsonify({"error":str(e)}), 400

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}),500



@user_blueprint.route('/user_subreddits', methods=['GET'])
@jwt_required()
def fetch_user_subreddits():
    user_id = int(get_jwt_identity())
    subreddits = getUserSubredditsService(user_id)
    return jsonify({"users_subreddits": subreddits}), 200