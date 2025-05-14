from ..Engine import *
from flask import Blueprint, request,jsonify
from ..CustomException import *
from flask_jwt_extended import jwt_required,get_jwt,get_jwt_identity

search_blueprint = Blueprint('search', __name__, url_prefix='/search')
redis_client = get_redis_client()


BASE_TTL = 60 * 60 * 2           # manji popularni sub, TTL  
EXTENDED_TTL  = 60 * 60 * 6          # vise popularni sub , TTL 6h
POPULARITY_THRESHOLD = 10        # Minimum members to consider for Redis Posle cu ove brojeve adjustovati na vece brojeve
HIGH_POPULARITY_THRESHOLD = 100  # Threshold for extra long TTL


#za search nece trebati jwt token jer svaki user moze da pretrazi reddit i da nadje subreddit ili usere
@search_blueprint.route('/suggest', methods=['GET'])
def search_suggestions():
    data = request.get_json()
    query = data["query"]
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    #preko fronta cemo dodati Debouncing i highlitgh imas u notepadu napisano

    #za paginaciju posle...
    page = int(data.get("page", 1))  # Default page 1
    limit = int(data.get("limit", 10))  # Default limit 10 items per page
    # Calculate the offset for pagination (determines the starting index of results)
    offset = (page - 1) * limit

    #kako paginacija funkcionise
    #page na kojoj smo strani, limit kolko subreddita max useru prikazujemo
    #offset -> page 1 -> 1 - 1 * 10 -> 0  znaci krecu od 0 indeksa pa do limita,
    # page 2 -> (2-1)*10 -> 1*10 ->  cached_results[offset:offset + limit]-> [10:10+10] -> tj pokupi indeks od 10 do 20 tj narednih 10 sa page 2


    #Pokusamo da metchujemo sa cachom iz redisa

    # Redis storuje subreddits as 'id|name', i uzimamo i score tj broj membera
    cached_results = redis_client.zrangebyscore('popular_subreddits', '-inf', '+inf', withscores=True)

    # Filter baziran na second part tj imenu subredita postu ovom redisu cuvam id|name jer ne moze drugacije onda moram ovako
    filtered_results = [
        {"id": res.split('|')[0], "name": res.split('|')[1], "score": score}
        for res, score in cached_results
        if res.split('|')[1].lower().startswith(query.lower())
    ]   
     
    # Ako je cache hit, returnujemo cashovane subreddits sa pagination
    if filtered_results:
        return jsonify({
            "results": filtered_results[offset:offset + limit],
            "page": page,
            "limit": limit,
            "total_results": len(filtered_results)
        })
    

    #Ako ga nema u cache-u onda moramo do DB otici
    subreddits = FetchPopularSubredditsService(query)

    if not subreddits:
        return jsonify({"message": "No subreddits found"}), 404
    
    #Stavljamo u redis samo za one subbredite koji imaju odredjeni broj membera,  i dodajemo TTL, 
    for subreddit in subreddits:
        key = f"{subreddit['id']}|{subreddit['name']}"
        member_score = subreddit['member_count']

        if member_score > POPULARITY_THRESHOLD:
            redis_client.zadd("popular_subreddits", {key: member_score})

            if member_score > HIGH_POPULARITY_THRESHOLD:
                redis_client.expire(key, EXTENDED_TTL)
            else:
                redis_client.expire(key, BASE_TTL)


    # Paginate resultove from the database (now in memory)
    total_results = len(subreddits)
    paginated_results = subreddits[offset:offset + limit]


    return jsonify({
        "results": paginated_results,
        "page": page,
        "limit": limit,
        "total_results": total_results
    })
