
# In UsersDBHandler.py
from .DataBaseStart import *
from Backend.CustomException.CustomExceptions import *
#ovako podeljeni fileo-vi i sloj api,service, db je prvi princip SOLID-a , single responsability


def RegisterUser(user:dict):

    #hesiranje sifre cemo u service-u uraditi
    #sql injection u service-u isto kontam proveriti

    #ovde ce biti exception ako vec postoji User sa ovim username-om

    username      =  user["username "]
    email         =  user["email"]                          #nez dal da napravim na email-u kao da mu posaljem unique broj za potvrdu
    password_hash =  user["password_hash"]                  # i onda ako dobro unese taj broj na web-u da mu dam da bude registrovan


    query = """
     INSERT INTO Users (username, email, password_hash) 
     VALUES ('%s', '%s, '%s')
    """

    values  = (username,email,password_hash)
    
    connection = getConnection()

    cursor = connection.cursor()

    try:
        cursor.execute(query,values)                    #parametrizovani sql upiti MySql connector insertuje vrednosti u qeurry i provera da li ima SQL injectiona
        connection.commit()
        return True
    
    except mysql.connector.IntegrityError as err:
        connection.rollback()                           #da vratimo bazu u stanje pre nego sto je transakcija pocela, ako postoji duplikat sprecavamo da insertion izvrsi o ostavljamo bazu ne promenjenu
        if err.errno ==1062:
            raise IlegalValuesException("Username/Email already exists")
        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")
        
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while adding the profile.") 
    finally:
        cursor.close()
        release_connection(connection)






