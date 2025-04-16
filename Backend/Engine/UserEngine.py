
from ..Database import *                #importujemo DataBase Handlere, tu se nalazi RegisterUser
import bcrypt
import re

#treba koristii
def HashPassword(password:str)->str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'),salt)      #encoduje se u byte
    return hashed_password.decode('utf-8')  #da ga vratimo iz byte-a u string da bi mogao u bazi da bude storovan


def RegisterUserService(user:dict):


    #exception za duzinu sifre
    #exception za duzinu email-a
    #exception regex za email

    #nez dal da napravim na email-u kao da mu posaljem unique broj za potvrdu
    # i onda ako dobro unese taj broj na web-u da mu dam da bude registrovan

    if len(user["password"]) > 256 or len(user["password"]) < 8:
        raise IlegalValuesException("Password does not meet the minimum/maximum length requirement.")
    
    # Exception for username length
    if len(user["username"]) > 50:
        raise IlegalValuesException("Username does not meet the maximum length requirement.")
    
    # Exception for email length
    if len(user["email"]) > 100:
        raise IlegalValuesException("Email does not meet the maximum length requirement.")
    
    # Email regex validation
    if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user["email"]) is None:
        raise IlegalValuesException("Email does not meet the requirement.")



    password_hash = HashPassword(user["password"])

    user_checked = {
        "username":user["username"],
        "email": user["email"],
        "password_hash": password_hash
        }

    RegisterUser(user_checked)                  #poziv DataBase Layer-a


def LoginUserService(user:dict):

    #user["password"] = HashPassword(user["password"])   NE TREBA DA SE HASHUJE SIFRA ZBOG SALT-a ONDA SE NIKAD NECE POREDITI ISTI HASH CAK I AKO SE UNETA SIFRA POKLAPA SA DB sifrom 
    return GerUserCredentials(user)                     #DB sloj vraca dict tip, ako je sve ok vratice user-a sa infom







