import { useParams } from "react-router-dom";       
/* useParams hook sto nam dozvoljava da pristupimo route parametrima iz trenutnog URL-a
    u App.js -> <Route path="/r/:subreddit" element={<Subreddit />} />
    :subreddit je part od URL parametra , ako user se navigatuje to r/react -> vred subreddit-a je react


    kako useParams radi, 
    -Vraca objekat sa svim parametrima definisanim u Route
*/
const Subreddit = () =>{
    const {subreddit} = useParams();
    return <h1>Subreddit: {subreddit}</h1>;
};

export default Subreddit;