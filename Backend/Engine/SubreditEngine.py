from ..Database import *



def CreateSubbreditService(subreddit:dict):
    #excepiton za duzinu imena subredita
    #excepiton za duzinu descriptiona tipa 200 slova tako nes
    

    if len(subreddit["name"] >100) or len(subreddit["name"]==0):
        raise IlegalValuesException("Subreddit name does not meet the minimum/maximum length requirement.")
    
    if len(subreddit["description"] >200):
        raise IlegalValuesException("Subreddit description does not meet the maximum (200 characters) length requirement.")
    elif len(subreddit["description"]<1):
        raise IlegalValuesException("Subreddit description does not meet the minimum (1 characters) length requirement.")
    
    if not subreddit["created_by"]:
        raise IlegalValuesException("There is an error with admin_id creating this subreddit")
    #saljemo ka db sloju
    CreateSubbredit(subreddit)
    

#ovo API za search poziva kada cache missujemo subreddit
def FetchPopularSubredditsService(query:str):
    if len(query)>100:
        raise IlegalValuesException("Max len of subreddits names are 100 chars")
    return FetchPopularSubreddits(query)
     
