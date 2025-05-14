from ..Database import *
from extensions import get_redis_client


redis_client = get_redis_client()


#smanji radi provere da li radi
SYNC_INTERVAL = 60*60  # 1 sat, 3600 u sekundama definise kolko cesto cemo dodavati u reddis subreddite
TTL = 60 * 60 * 2        # 2 sata za TTL u reddis memoriji

#za suggesiton search u search bar-u fokusiracemo se na matchovanje najpopularnijih subbredit-a sa onim sto user u unese
def UpdatePopularSubreddits_cache_Service():
    """
    Periodicno updejtuje popularne subbredite u Redis cache. Popularnost se meri na osnovu membera/postova/ i jos neceg smislicu
    Izbacuje inactive or deleted subreddits.
    """
    while True:
        #ovde su najveziji popularni subrediti
        subreddits = FetchPopularSubredditsCache()

        if not subreddits:
            #nema subbredita pa cekamo
            time.sleep(SYNC_INTERVAL)                  # Wait for the next interval and skip this iteration
            continue


        #uzimamo prethodne popularne iz subredite iz cache-a
        current_keys =set(redis_client.zrange('popular_subreddits',0,-1))   #od 0 do -1 pokupimo ih sve i konvertujemo u set radi brze pretrage

        #set za cuvanje subreddit kljuceva, poslecemo razliku subreddita tj one koji nisu vise u db aktivni cemo removovati iz reddisa
        db_keys = set()

        #prolazimo kroz subreddite i updejtujemo reddis ako je potrebno

        for subreddit in subreddits:
            key = f"{subreddit['id']}|{subreddit['name']}"  #formatuje key kao  "id|name"
            db_keys.add(key)

            #uzmemo prethodni score i updejtujemo ga sa novim ako je novi veci
            current_score = redis_client.zscore('popular_subreddits', key) or 0  
            member_score = subreddit['member_count']     # member_count sam u querry podesio
            if key not in current_keys or member_score > current_score:
                redis_client.zadd('popular_subreddits', {key: member_score})

                if redis_client.ttl(key) == -1:      #ako je vec postavljen TTL da ga ne resetujemo opet
                    redis_client.expire(key, TTL)    #<-- Setujemo TTL od 2 hours, individualni TTL
                """
                Generalni    TTL: redis_client.expire('popular_subreddits', 4500)
                Individualni TTL: redis_client.expire(key, 4500)  # 75 minutes

                Sta je bolje, bolji je individualni jer TTL setujemo svaki za zaseban kljuc (it gets removed 75 minutes after its last update)
                Generalni ima problem da prilikom updejta makar jednog od kljuceva updejtuje se TTL svih kljuceva sto je lose, Individualni nam pruza 
                da npr pojedinacno budu removovani kljucevi a ne svi odjednom
                """  
                print(f"[Daemon] Updated or added: {key} with score {member_score}")
   


        #Poslednji korak removujemo subreddite koji nisu vise u DB-u

        #Pronadjemo kljuceve koji postoje u Reddisu ali ne i u DB-u
        #EdgeCase ako je u DB obrisan kljuc on ostaje u Reddisu pa cemo to popraviti sa TTL i jos ubrzamo tako sto explicitno taj key deletujemo iz reddi-sa u for loop-u dole
        subreddits_to_remove = current_keys - db_keys
        # ako treba removati neki subreddit
        if subreddits_to_remove:
            #zasto * treba, odgovor sa chat gpt-a
            # redis_client.zrem() needs to be unpacked into separate arguments.
            # subreddits_to_remove is: {'1|python', '2|flask', '3|django'} a treba nam '1|python', '2|flask', '3|django'
            # to * uradi                         
            redis_client.zrem('popular_subreddits', *subreddits_to_remove)  

            redis_client.delete(*subreddits_to_remove) # <-- Ekplicitno obrisemo key koji vise nije u DB iz redis memorije !

        #u principu redis je thread safe po defaultu jer svaka operacija zadd,zrangebylex je atomicna na reddis serveru i reddis interno handluje konkurentnost i garantuje atomicnost
        #JEdini mali problem sa moje strane moze biti race condition threada za operaciju UpdatePopularSubreddits_cache_Service  kada se removuje key
        # dok /suggest cita podatke iz redisa ali to ce usporiti za nekoliko milisekundi sto je okej i prihvatljivo osim ako mi ne treba 100% konz, a mogu ovo dodati kasnije

        #spavanje
        time.sleep(SYNC_INTERVAL)                        