from .DataBaseStart import *
from ..CustomException import *


def CreatePost(post:dict):
    #treba da proverimo da li je user member subredita da bi mogao da postujemo, uradicemo to u okviru 1 konekcije da ne bi smo trosili vreme konekcije
    query_check_membership = """
        SELECT 1 from members WHERE user_id = %s AND subreddit_id = %s
    """
    query_insert_post ="""
    INSERT INTO posts (title, content, created_by, subreddit_id)
    VALUES (%s, %s, %s, %s)
    """

    title=post["title"] 
    content =post["content"] 
    created_by =post["created_by"]
    subreddit_id = post["subreddit_id"]
    #upvotes=0 default je 0

    connection = getConnection()
    cursor = connection.cursor()

    try:

        #Prvo proverimo da li je user member subreddita ako jeste onda moze da postuje
        cursor.execute(query_check_membership,(created_by,subreddit_id))
        if cursor.fetchone() is None:
            raise IlegalValuesException("User is not a member of the subreddit.")

        cursor.execute(query_insert_post ,(title,content,created_by,subreddit_id))
        connection.commit()
    
    except mysql.connector.IntegrityError as err:
        connection.rollback()

        #ovo je ForeignKeyCointrant broj, da bi mogao 
        if err.errno == 1452:
            if "created_by" in str(err):
                raise IlegalValuesException("The user specified does not exist.")
            elif "subreddit_id":
                raise IlegalValuesException("The specified subreddit does not exist.")

        #U slucaju drugih error-a
        raise IlegalValuesException(str(err))
    

    except mysql.connector.OperationalError:
        connection.rollback()
        raise ConnectionException("An error occurred while adding the post.")
    finally:
        cursor.close()
        release_connection(connection)

