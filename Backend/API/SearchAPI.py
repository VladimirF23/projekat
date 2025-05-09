from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *
from flask_jwt_extended import jwt_required,get_jwt,get_jwt_identity

search_blueprint = Blueprint('search', __name__, url_prefix='/search')
redis_client = get_redis_client()


CACHE_TTL = 60 * 60     #za suggestion


@search_blueprint.route('/suggest', methods=['GET'])
def search_suggestions():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    #preko fronta cemo dodati Debouncing i highlitgh imas u notepadu napisano

    #za paginaciju posle...
    page = int(request.args.get('page', 1))  # Default page 1
    limit = int(request.args.get('limit', 10))  # Default limit 10 items per page
    # Calculate the offset for pagination (determines the starting index of results)
    offset = (page - 1) * limit

    #Pokusamo da metchujemo sa cachom iz redisa

    # Redis storuje subreddits as 'id|name'
    cached_results = redis_client.zrangebylex('popular_subreddits', f"[{query}", f"[{query}\xff") #zrangebylex je kao neki brzi substring matcher
    # Ako je cache hit, returnujemo cashovane subreddits sa pagination
    if cached_results:
        return jsonify({
            "results": cached_results[offset:offset + limit],
            "page": page,
            "limit": limit,
            "total_results": len(cached_results)
        })
    

    #Ako ga nema u cache-u onda moramo do DB otici
    subreddits = fetch_popular_subreddits(query)

    if not subreddits:
        return jsonify({"message": "No subreddits found"}), 404
    
    #Stavljamo u redis Cache i dodajemo TTL
    for subreddit in subreddits:
        key = f"{subreddit['id']}|{subreddit['name']}"
        member_score = subreddit['member_count']
        redis_client.zadd(CACHE_KEY, {key: member_score})
        redis_client.expire(key, TTL)


    # Paginate resultove from the database (now in memory)
    total_results = len(subreddits)
    paginated_results = subreddits[offset:offset + limit]


    return jsonify({
        "results": paginated_results,
        "page": page,
        "limit": limit,
        "total_results": total_results
    })
