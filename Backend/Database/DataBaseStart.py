import mysql.connector
import json
import logging
from mysql.connector import pooling
from dotenv import load_dotenv
import os
import time

from ..CustomException import *

connection_pool = None
# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "devinfo.env"))

# Retrieve variables from the environment

#Da ne bi uplodovali na github devInfo ovako uzimamo i cuvamo info, u gitignore dodamo .env
DB_HOST = os.getenv("DB_HOST")      #u .env umesto localhost sada koristimo ime service(container-a) i to je mysql
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT =  int(os.getenv("DB_PORT"))
POOL_NAME = os.getenv("POOL_NAME", "mypool")  # You can also fetch pool name from .env
POOL_SIZE = int(os.getenv("POOL_SIZE", 10))  # Default pool size to 10 if not defined

def initializePool():
    global connection_pool
    try:
        if connection_pool is None:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name=POOL_NAME,
                pool_size=POOL_SIZE,
                host = DB_HOST,
                user = DB_USER,
                port = DB_PORT,
                password =DB_PASSWORD,
                database = DB_NAME
                )

    #mi cemo kod API-ja hvatati ovaj exception i returnovati  return jsonify({"error": "Internal server error. Please try again later."}), 500
    except Exception as e:
        logging.error(f"Error initializing connection pool: {e}", exc_info=True)
        raise Exception("Failed to initialize database connection pool") from e
    


def getConnection(max_tries =6, timeout=0.5):
    global connection_pool
    if connection_pool is None:
        initializePool()

    tries=0

    while tries<max_tries:
        try:
            #ovde pokusavamo da dobijemo konekciju iz pool-a
            return connection_pool.get_connection()                 #posto je globalna prom u inicijalizaciji se connection_pool = pooling.MySQLConnectionPool(...) uradi 
        except mysql.connector.Error as e:
            tries+=1
            logging.error(f"Attempt {tries}/{max_tries}: Connection pool exhausted. Error: {e}")
            time.sleep(timeout)

    logging.error(f"Failed to get a connection from the pool after {max_tries} retries.")
    raise Exception("Failed to get a connection from the pool after multiple retries.")



def release_connection(connection):
    try:
        if connection and  connection.is_connected():
            connection.close()
            logging.info("Connection released successfully.")
        else:
            logging.warning("Connection was already closed or invalid.")
    except mysql.connector.Error as e:
        logging.error(f"Error while releasing connection: {e}")




initializePool()
