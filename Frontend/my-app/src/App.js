
import React, {useEffect} from 'react';
import { Provider,useDispatch } from 'react-redux';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import store from './app/store';

import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Subreddit from "./pages/Subreddit";
import Post from "./pages/Post";
import ProtectedRoute  from "./components/ProtectedRoute";
import NotFoundPage from "./pages/NotFoundPage"; 
import AccessDeniedPage from './pages/AccessDeniedPage';

//za redus stanje
import { authCheckStart,loginSuccess,logout,authCheckComplete } from './features/authorization/authSlice';
//API
import axiosInstance from './api/axiosInstance';
import { logoutUser } from './api/authApi';



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


// primereri dummy component-a za protektovane page-ove
const Dashboard = () => <h2>Welcome to your Dashboard! (Protected)</h2>;
const AdminPage = () => <h2>Welcome, Admin! (Admin Only)</h2>;


const AppContent  = () => {
  const dispatch = useDispatch();


// Effect to run once on component mount to check initial authentication status
  useEffect(() => {
    const checkAuthStatus = async() =>{
      dispatch(authCheckStart());       // Postavimo loading na true, clear errors

      try{
        // This call will send the HttpOnly access token cookie automatically
        const userDetailsResponse = await axiosInstance.get('/api/auth/me');
        const userDetails = userDetailsResponse.data;
        dispatch(loginSuccess(userDetails)); // User is authenticated, set details


      }catch(error){
        // Ako /api/auth/me return-uje 401 (ili nesto drugo) znaci da nije validna sesija
        // axios interceptor ce pokusati da refresh token
        // mislim da mi ovo ni ne treba
        // Ako i to fail-uje on ce dispatch-ovati logoutAction().
        // Ovde osiguramo logout ako nema user details
        console.log("Initial auth check failed, user not logged in or token invalid.", error);
        dispatch(logout())

        try {
          await logoutUser();     // opcionalno: osiguramo da je  server-side cist
        } catch (apiLogoutError) {
          console.error("API logout during initial check failed:", apiLogoutError);
        } 

      }finally{
        dispatch(authCheckComplete()) // Postavimo loading na false za svaki outcome
      }

      
    };
    checkAuthStatus();
  }, [dispatch]);

  return( 
  <Router>
    <Navbar/>   {/*Da uvek bude vidljiv */}
    <Routes>
      <Route path="/" element={<Home />} />          
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/403" element={<AccessDeniedPage />} /> {/* novi 403 page */}


      {/*Public Routes sa Dimamickim Parametrima */}
      <Route path="/r/:subreddit" element={<Subreddit />} />
      <Route path="/r/:subreddit/:postId" element={<Post />} />


      {/* --- Protected Routes --- */}
      {/* Bilo koji route nestovan ovde ce zahtevati autentifikaciju */}
      <Route element={<ProtectedRoute />}>
      <Route path="/dashboard" element={<Dashboard />} />
      {/* Add more protected routes here */}
       {/* Primer: <Route path="/create-post" element={<CreatePostPage />} /> 
                  <Route path ="/myProfile" ..../>
       */}
      </Route>

      {/* --- Admin-only Protected Route --- */}
      {/* Ova route zahteva oba authentication I admin privileges */}
      <Route element={<ProtectedRoute adminOnly={true} />}>
          <Route path="/admin" element={<AdminPage />} />
      </Route>

      {/* Optional: Add a 404 Not Found page */}
      <Route path="*" element={<NotFoundPage />} />




    </Routes>
  </Router>
  );
};


//  main App component sada wrapuje AppContent sa Redux Provider
const App = () => (
    <Provider store={store}>
        <AppContent />
    </Provider>
);
export default App;   //da bi App component dostupan za korisceneni u drugim partovima aplikacije  
