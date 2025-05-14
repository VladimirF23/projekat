from .DataBaseStart import *
from ..CustomException import *




def CreateSubbredit(subreddit:dict):
    name = subreddit["name"]
    description = subreddit["description"]
    created_by = subreddit["created_by"]

    querry="""
    INSERT INTO subreddits (name,description,created_by)
    VALUES (%s,%s,%s)
    """

    connection = getConnection()

    cursor = connection.cursor()

    try:
        cursor.execute(querry,(name,description,created_by))
        connection.commit()                                     #mozda mora ovo da bi se ubacilo u tabelu skroz

    except mysql.connector.IntegrityError as err:
        connection.rollback()

        if err.errno ==1062:
            raise IlegalValuesException("Subredit name already exists")
        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while adding the subreddit.") 
    finally:
        cursor.close()
        release_connection(connection)



#u principu ni reddit ne vraca 100 predloga za subreddite kada user ukuca u subreddit nesto
#pa je isto dobro da ih sortiramo kao po nekom popularitiju tipa da prikazemo samo 15 najpopularnijih koji matchuju input search-a
def FetchPopularSubreddits(query, limit=15):
    """
    Ovu funkciju pozivamo u search-u kada nam failuje cache hit pa moramo da pristupamo bazi
    Vracamo subbreddite iz DB tako da im name matchuje search query, sortirani su po popularanosti.
    Args:
        query (str): search query da matchuje subreddit names.
        limit (int): max broj rezultata kojih vracamo user-u (default is 15). 
    Returns:
        list: listu dictionaries koji sadrze subreddit info.
    """

    #ne mesaj query sa query db-om

    query_db = """
            SELECT s.id, s.name, COUNT(m.user_id) as member_count
            FROM subreddits s
            LEFT JOIN members m ON s.id = m.subreddit_id
            WHERE s.name LIKE %s OR s.name = %s
            GROUP BY s.id, s.name
            ORDER BY member_count DESC
            LIMIT %s
        """
    connection = getConnection()
    cursor = connection.cursor(dictionary=True)

    search_pattern = f"{query}%"  # 'regex' koji ce nam matchovati prefix ako se matchuje al cu proslediti u query_db ceo querry da moze da matchuje i celo ime 
    try:
        cursor.execute(query_db, (search_pattern,query, limit))     #i query sam prosledio
        subreddits = cursor.fetchall()
        return subreddits
    except mysql.connector.OperationalError as err:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while adding the subreddit.") 
    finally:
        cursor.close()
        release_connection(connection)