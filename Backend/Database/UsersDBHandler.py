
# In UsersDBHandler.py
from .DataBaseStart import *
from ..CustomException import *
import bcrypt
#ovako podeljeni fileo-vi i sloj api,service, db je prvi princip SOLID-a , single responsability


def RegisterUser(user:dict):

    #hesiranje sifre cemo u service-u uraditi
    #sql injection u service-u isto kontam proveriti

    #ovde ce biti exception ako vec postoji User sa ovim username-om

    username      =  user["username"]
    email         =  user["email"]                          #nez dal da napravim na email-u kao da mu posaljem unique broj za potvrdu
    password_hash =  user["password_hash"]                  # i onda ako dobro unese taj broj na web-u da mu dam da bude registrovan


    query = """
     INSERT INTO users (username, email, password_hash) 
     VALUES (%s,%s,%s)
    """

    
    connection = getConnection()

    cursor = connection.cursor()

    try:
        cursor.execute(query,(username,email,password_hash))                    #parametrizovani sql upiti MySql connector insertuje vrednosti u qeurry i provera da li ima SQL injectiona
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
        raise ConnectionException("An connection error occurred while registering the user.") 
    finally:
        cursor.close()
        release_connection(connection)



    



#Fora sa ovim je prilikom logovanja da bi proverili password ne mozemo koristiti onaj hash jel tu ima salt-a i onda
#ce taj salt cak i za dobru unetu sifru je promenuti i nece valjati pa cemo koristiti nes sepcijalno od bcrypt
def GerUserCredentials(userCredentials: dict):

    #ako nije registrovan digni NotFoundException i stavi user not registered 
    query = """
        SELECT id,password_hash, username, email, global_admin
        FROM users
        WHERE username = %s;
    """
    #u qeurry proveravamo prvo username dal postoji ako postoji onda izvlacimo hashiranu sifru da proverimo da li je dobra sa unetom sifrom
    username = userCredentials["username"]
    entered_pass= userCredentials["password"]


    connection = getConnection()
    cursor = connection.cursor(dictionary=True)         #ovde ga konvertujemo automatski da vrati kao dict

    try:
        cursor.execute(query,(username,))

        #fetcone vraca kao tuple pa cemo ga konvertovati u dict, lakse je preko dict jer pristupam sa imenima kolona, a ne ono indkesovano 0,1,2,3
        #i jos je JSON ready jer mogu onda direkt da ga vratim direkt ka FLASK-API response preko jsonify
        user = cursor.fetchone()
        if not user:
            raise NotFoundException("Username/password not valid")
        

        #ovo je izvuceno iz mysql
        db_hashed = user["password_hash"]

        if not bcrypt.checkpw(entered_pass.encode("utf-8"), db_hashed.encode("utf-8")):
            raise NotFoundException("Username/password not valid")

        del user["password_hash"]

        #brisemo da ne bi API response bio presreten ili logovan
        #zbog preksravanja least privlage-a tj frontend ne treba da interesuje sifra


        #vracamo user info
        return user
    

    finally:
        cursor.close()
        release_connection(connection)


#hmm ako je vec joinovao onda bi treba da napusti ali msm da preko fronta mogu da namestim da se promeni ikonica
def joinSubreddit(user_id:int, subreddit_id:int):
    querry="""
    INSERT INTO members (user_id,subreddit_id)
    VALUES (%s,%s)
    """
    #koristi se %s za parameterozovane placeholdere nbtno dal je int tipa 
    connection = getConnection()

    cursor = connection.cursor()

    try:
        cursor.execute(querry,(user_id,subreddit_id))
        connection.commit()

    except mysql.connector.IntegrityError as err:
        connection.rollback()

        if err.errno ==1062:
            raise IlegalValuesException("User already joined that subreddit")
        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")


        #ovo je u slucaju foreign key contraint-a tj da ne postoji subbredit kom zelimo da pristupimo mysql zbog foreign key-a moze da proveri u tabeli subbredit da li postoji taj id
        raise IlegalValuesException(str(err)) 

    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while adding joining subreddit.")
    finally:
        cursor.close()
        release_connection(connection)

def leaveSubreddit(user_id:int, subreddit_id:int):
    querry="""
    DELETE FROM members
    WHERE user_id=%s and subreddit_id=%s
    """
    connection = getConnection()

    cursor = connection.cursor()
    try:
        cursor.execute(querry,(user_id,subreddit_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise IlegalValuesException("User is not a member of that subreddit.")
    except mysql.connector.IntegrityError as err:
        connection.rollback()

        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")
        elif err.errno == 1452:         #FORENG KEY COINSTRANT
            raise IlegalValuesException(str(err))


    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while adding joining subreddit.")
    finally:
        cursor.close()
        release_connection(connection)


def returUsersSubreddits(user_id:int):
    querry="""
    SELECT s.id, s.name, s.description, s.created_by, m.joined_at
    FROM members m
    JOIN subreddits s ON m.subreddit_id = s.id
    WHERE m.user_id = %s;
    """

    connection = getConnection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(querry,(user_id,))
        subreddits = cursor.fetchall()
        return subreddits
    except mysql.connector.IntegrityError as err:
        connection.rollback()
        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")      
         
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while adding joining subreddit.")

    finally:
        cursor.close()
        release_connection(connection)

#originalno je bila napravljena za createPost ali da ne bih milion konekcija sa DB ovu cu funkciju koristiti za druge stvari
def is_user_member_of_subreddit(user_id:int, subreddit_id:int)->bool:
    querry= """
        SELECT 1 from members WHERE user_id = %s AND subreddit_id = %s
    """
    connection = getConnection()
    cursor = connection.cursor()
    #SELECT queries do not trigger foreign key checks — they simply try to find a matching row.
    # ne moram da brinem of Foreign Key constraintu tamo gore u joinovanju JOIN i leavovanju DELETE row
    try:
        cursor.execute(querry,(user_id,subreddit_id))
        result = cursor.fetchone()
        return result is not None
    
    except mysql.connector.IntegrityError as err:
        connection.rollback()
        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")     
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException(str(err))
    finally:
        cursor.close()
        release_connection(connection)

