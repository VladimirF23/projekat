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



