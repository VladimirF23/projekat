from ..Database import *                





def createPostService(post:dict):

    if not isinstance(post["subreddit_id"], int):
        raise IlegalValuesException("Subreddit ID must be an integer.")
    if not post["title"] or len(post["title"]) > 255:
        raise IlegalValuesException("Title must be provided and cannot exceed 255 characters.")
    if not post["content"]:
        raise IlegalValuesException("Content cannot be empty.")
    
    
    CreatePost(post)                                   
