import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Subreddit from "./pages/Subreddit";
import Post from "./pages/Post";

/*
React Router biblioteka koja omogucava routing u React app-u, dozvoljava app-u da prikaze razl pages (Home,Register,Login,Subreddit,post) preko URL u browser-u
handluje navigaciju i renderovanje komponenata tako da se ne primeti ->npm install react-router-dom

BrowserRouter as Router:
  -main routing component koja enabluje routing u mom app-u. Gleda promene URL-a i renderuje na odgovarajuce components
Route:
  -Definise individualne routes koji mapiraju specificne path-ove (/login,/register) na odgovarajuci React Component
Routes:
  - Wraper za group-ovanje vise <Route> components

Ja importujemo moje page components(Home,Login..) from pages Directory


*/

/*Svaki <Route> component definise path i component da renderuje
  Kada URL path match-uje '/' renderovace <Home> component, element= nam govori koju komponentu treba renderovati

  Dynamic Routes:
  :subreddit i :postId su route parameters, Oni su placeholderi za dynamic values u URL-u
  Primer:
    Ako posetim /r/javascript , <Subreddit/> component se renderuje i subreddit ce biti "javascript"
    Ako posetim /r/javascript/123, <Post> component se renderuje sa subreddit="javascript" i postId =123


    Mogu da pristupim ovim parametrima unutar componenta koristeci useParams hook ovako
    import { useParams } from "react-router-dom";

  const Subreddit = () => {
    const { subreddit } = useParams();
    return <h1>Welcome to {subreddit} subreddit!</h1>;
}

*/
const App = () => (
  <Router>
    <Navbar/>   {/*Da uvek bude vidljiv */}
    <Routes>
      <Route path="/" element={<Home />} />          
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/r/:subreddit" element={<Subreddit />} />
      <Route path="/r/:subreddit/:postId" element={<Post />} />
    </Routes>
  </Router>
);

export default App;   //da bi App component dostupan za korisceneni u drugim partovima aplikacije  
