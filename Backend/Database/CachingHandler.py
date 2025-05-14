from .DataBaseStart import *
from ..CustomException import *


#za cachiranje
#limit je 50 da ne bi smo sve kljuceve stavili u reddis, i zato ima smisla da ih sortiramo opadajuce po broju membera
def FetchPopularSubredditsCache(limit=50):
    """
    Fetches the list of top `limit` subreddits and their member count from the database.
    """

    query = """
            SELECT s.id, s.name, COUNT(m.user_id) as member_count
            FROM subreddits s
            LEFT JOIN members m ON s.id = m.subreddit_id
            GROUP BY s.id, s.name
            ORDER BY member_count DESC
            LIMIT %s
        """
    connection = getConnection()
    cursor = connection.cursor(dictionary=True)
    try:

        cursor.execute(query, (limit,))
        popular_subreddits = cursor.fetchall()
        return popular_subreddits

    except mysql.connector.OperationalError:
        connection.rollback()
        raise ConnectionException("An error occurred while adding the post.")
    finally:
        cursor.close()
        release_connection(connection)
