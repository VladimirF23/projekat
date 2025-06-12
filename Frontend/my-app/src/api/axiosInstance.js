import axios from 'axios';
import Cookies from 'js-cookie';

// refresh token function iz  authApi
import { refreshToken, logoutUser } from './authApi';                 // ovo je za API, tj da na serveru zovemo API
import store from '../app/store';                                    // redux store

import { logout as logoutAction,loginSuccess } from '../features/authorization/authSlice'; // ovo za redux store tj stanje na front-u da ocisitmo


/*
    Axios HTTP client library koristi se za pravljenje asynchronous requests ka external APIs or backend service-ima: 

    dozvoljava:
        -Slanje HTTP zahteva,Mozemo saljemo GET,POST,DELETE,PUT request-ove da komuniciraju sa serverom
        -Handle responses - Daje metode da Handluje Response od servera npr JSON data i status codo-ve
        -Error Handling   - axios automatski cachira errore i daje da ih handlujemo sa .catch
        -Promise based    - Baziran na JS promises, koji olaksavaju rad sa async operacijama
        -Iterceptors      - Mozemo da interceptujemo requests ili responses pre nego sto su obradjeni, sto olaksava logovanje i global error handling
        -Support za Cancel Req  - canculujemo request ako vise nije potreban
        -Headers i Autorizacija - lako setuje header-e za authentifikaciju (kao JWT tokena) ili custom header-a
        

*/

//instanca axios-a
const axiosInstance = axios.create({
    baseURL: 'https://localhost',                //Ne ovako: 'http://localhost:5000' Moj React app runuje na 3000, Nginx on 80/443, Flask na 5000 unutar svog container, Moj React app uvek treba da prica sa Nginx, ko onda proxies ka Flask
                                                 //stavimo da pointuje ka Nginx-u!  U produkciji moj domain, e.g., 'https://api.yourdomain.com'
    headers:{
        'Content-Type': 'application/json',          //govori serveru da ce axios slati podatke u JSON formatu
    },
})

// REQUEST interceptor
// Svi state change-ing request-ovi (PUT,POST,DELETE) ce zahtevati custom csrf token u custom header-u, ovaj token je dostupan u JS readable cookie csrf_token
//treba mi axios interceptor da procita ovaj token i da ga doda na svaki state changing request
axiosInstance.interceptors.request.use(
    (config) =>{
        //procitamo CSRF token iz csrf_token cookie-a
        const csrf_token = Cookies.get('csrf_token');
        
        //ako postoji csrf token i state changing je metoda dodaj ga u header
        if (csrf_token && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method.toUpperCase())){
            config.headers['X-CSRF-TOKEN'] = csrf_token;         // Flask-JWT-Extended default header ime

        }

        return config;

    },
    (error) =>{
        return Promise.reject(error);
    }
);

// Ovaj RESPONSE interceptor hvata sve respons-ove a ispitujemo one koji imaju error i to gledamo na 401 Unauthorized da proverimo da li treba silently 
// refreshovati access token, acces token kada istikne nakon 15 minuta automatski pri jwt_required se vraca Unauthorized pri narednom request-u
axiosInstance.interceptors.response.use(
    (response) => response,                         //Ako je uspesan onda pass-ujemo
    async (error) => {
        const originalRequest = error.config;
        // Kada bilo koji API return-uje 401 (Unauthorized) pokusava da pozove refreshToken, ako je uspesan refresh poziva /api/auth/me da dobije najazurnije
        // podatke za user-a (sebe) ovo radimo jer JTI od JWT HttpOnly Cooki-a ce biti razlicit od prethodnog (i mozda ce neki podaci biti drugaciji)
        // pa da bi Redux imao azurne podatke za trenutnu sesiju
        if (error.response && error.response.status === 401 && !originalRequest._retry) {

            // ovaj flag je bitan da sprecimo infinite loop za request, Ako ORIGINALNI request fail-uje opet nakon refresh attempt-a  ne zelimo
            // da on nastavi da pokusava da se refresh-uje  
            originalRequest._retry = true; 

            try {
                // Pokusaj da refresh-ujemo token, await refreshToken -> Ovo setuje novi HttpOnly cookies na browser-u
                await refreshToken();  

                // Posle uspesnog refresh-a treba da azuriramo podatke user-a 
                // zato sto novi Acces Token ima razlicit JTI i mozda nove/razl. claim-ove a stari podaci u Redux mogu biti zastareli
                // Ovo radimo jer refreshToken API ne vraca podatke o user-u
                const userDetailsResponse = await axiosInstance.get('/api/auth/me');
                const userDetails = userDetailsResponse.data;
                //store.dispatch(logoutAction());                  // Na FRONT-u (redux)ocisitmo state i updejtujemo Dispatch logout da ocistimo state pre postavljanja novih user details
                //store.dispatch(setUserDetails(userDetails));     //semanticki je tacnije samo da promenimo state jer to ovaj action radi a loginSuccses menja i isAuthenticated opet u True a to nema potrebe
                
                store.dispatch(loginSuccess(userDetails)); 

                // Pokusavamo originalani request sa novim validnim cookiem
                return axiosInstance(originalRequest);

            } catch (refreshError) {
                // Ako Refresh ne uspe (e.g refresh token istekao ili blacklisted)
                // log out user-a sa frontend-a
                console.error("Token refresh failed:", refreshError);
                store.dispatch(logoutAction());                         // Dispatch logout action to Redux store

                // Pozovemo API da osiguramo server-side invalidation ako treba (refresh failure uglavnom govori da je na serveru vec setovano)
                try {
                    await logoutUser(); // Na serveru da ocistimo
                } catch (logoutApiError) {
                    console.error("Logout API call failed after refresh failure:", logoutApiError);
                }
                // Redirect ka login page ovo uglavnom handluje React Router guard
                // ili global listener na isAuthenticated state.
                // hanldovacemo redirection u ProtectedRoute component.
                return Promise.reject(refreshError); // Propagiramo refresh error
            }
        }

        return Promise.reject(error); // za sve ostale error-e, samo re-throwujemo
    }

);


// Nece raditi posto HTTP only koristim i JS nece moci da cita iz cookia JWT
// //funkcija za set-ovanje tokena posle login-a i register
// export const setAuthTokenAxios = (token) =>{
//     if (token){                                                                     //ako postoji token (posle login-a i registera imati ) svakom requestu se dodaje  JWT token
//         axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
//         //dodaje se Authorization header svakom requstu i ovako izgleda Authorization: Bearer <Your_JWT_Token>


//     }else{
//         //ako ne postoji brise se authorization header
//         delete axiosInstance.defaults.headers.common['Authorization'];

//     }


// }

export default axiosInstance;
