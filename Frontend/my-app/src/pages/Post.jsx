import { useParams } from "react-router-dom";

const Post= () =>{
    const {subreddit,postId} = useParams()

    return(
        <h1>
            Post Page - Subreddit: {subreddit}, PostID {postId}
        </h1>
    )


};

export default Post;