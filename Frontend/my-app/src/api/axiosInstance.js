
//  /axiosInstance.js

import axios from 'axios';
import Cookies from 'js-cookie';

// refresh token function iz  authApi
import { refreshToken, logoutUser } from './authApi';                 // ovo je za API, tj da na serveru zovemo API
import store from '../app/store';                                    // redux store
import AuthError from '../utils/AuthError';
import { logout as logoutAction,loginSuccess,authCheckComplete } from '../features/authorization/authSlice'; // ovo za redux store tj stanje na front-u da ocisitmo


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
    withCredentials:true,

})


// Kreiraj *posebnu* Axios instancu samo za refresh token pozive
// Ova instanca NEMA prikačen glavni response interceptor, sprecava rekurzivnu petlju
export const refreshAxiosInstance = axios.create({
    baseURL: 'https://localhost', // Mora pokazivati na Nginx
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Obavezno za slanje HttpOnly kolačića
});




// REQUEST interceptor
// Svi state change-ing request-ovi (PUT,POST,DELETE) ce zahtevati custom csrf token u custom header-u, ovaj token je dostupan u JS readable cookie csrf_token
//treba mi axios interceptor da procita ovaj token i da ga doda na svaki state changing request
axiosInstance.interceptors.request.use(
    (config) =>{
        //procitamo CSRF token iz csrf_token cookie-a
        const csrf_token = Cookies.get('csrf_access_token');
        


        //ako postoji csrf token i nije refresh i login, onda dodaj csrf u header
        if (csrf_token && config.url!== '/auth/refresh' && config.url !== '/auth/login'){       //login ne treba da csrf token jer se user loguje prvi put
            
            config.headers['X-CSRF-TOKEN'] = csrf_token;         // Flask-JWT-Extended default header ime

        }

        return config;

    },
    (error) =>{
        return Promise.reject(error);
    }
);



// Flag za sprecavanje istovremenih pokusaja osvezavanja (debouncing)
let isRefreshing = false;
let failedQueue = [];

// Funkcija za obradu zahteva koji čekaju na osvezavanje tokena
const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};






// Ovaj RESPONSE interceptor hvata sve respons-ove a ispitujemo one koji imaju error i to gledamo na 401 Unauthorized da proverimo da li treba silently 
// refreshovati access token, acces token kada istikne nakon 15 minuta automatski pri jwt_required se vraca Unauthorized pri narednom request-u
axiosInstance.interceptors.response.use(
    (response) => response,                         //Ako je uspesan onda pass-ujemo
    async (error) => {
        const originalRequest = error.config;
        
        console.log("DEBUG: RESPONCE INTERCEPTOR POCETAK from /api/auth/me");

        
        // Izuzmi login i register rute iz ove logike interceptora
        // (npr. ako vraćaju 401 za pogresne kredencijale, ne zelimo da pokusamo refresh)
        if (originalRequest.url === '/auth/login' || originalRequest.url === '/auth/register') {
            return Promise.reject(error);
        }
        
        

        // **NOVA LOGIKA: Uhvati AuthError direktno ako dolazi od prethodnog pokusaja refresh-a**
        if (error instanceof AuthError && error.message === "Failed to refresh token") {
            console.error("DEBUG INTERCEPTOR: Prilagođena AuthError iz refresh funkcije uhvaćena. Forisrano odjavljivanje.", error); // Dodato logovanje
            
            isRefreshing = false;
            processQueue(error, null);

            store.dispatch(logoutAction());
            try { 
                await logoutUser(); 
            } catch (apiLogoutError) { 
                console.error("Logout API poziv nije uspeo nakon neuspeha refresh-a (očekivano za neautentifikovane):", apiLogoutError); 
            }
            
            // Perform hard redirect only AFTER all state cleanup is done
            if (window.location.pathname !== '/login') { // Prevent redundant redirect if already on login page
                window.location.href = '/login';
            }
            return Promise.reject(error);
        }



        
        // Kada bilo koji API return-uje 401 (Unauthorized) pokusava da pozove refreshToken, ako je uspesan refresh poziva /api/auth/me da dobije najazurnije
        // podatke za user-a (sebe) ovo radimo jer JTI od JWT HttpOnly Cooki-a ce biti razlicit od prethodnog (i mozda ce neki podaci biti drugaciji)
        // pa da bi Redux imao azurne podatke za trenutnu sesiju
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            console.log("DEBUG: RESPONCE INTERCEPTOR 3 IF ", error.response);



            // ovaj flag je bitan da sprecimo infinite loop za request, Ako ORIGINALNI request fail-uje opet nakon refresh attempt-a  ne zelimo
            // da on nastavi da pokusava da se refresh-uje  
            originalRequest._retry = true; 


            // Debouncing: Ako je refresh već u toku, dodaj zahtev u red čekanja
            if (isRefreshing) {
                return new Promise(function(resolve, reject) {
                    failedQueue.push({ resolve, reject });
                }).then(() => axiosInstance(originalRequest)).catch(err => Promise.reject(err));
            }

            isRefreshing = true; // Postavi flag: refresh je u toku

            try {
                // Pokusaj da refresh-ujemo token, await refreshToken -> Ovo setuje novi HttpOnly cookies na browser-u
                await refreshToken();  
                console.log("DEBUG: Pokusaj refresh-a ");

                // Posle uspesnog refresh-a treba da azuriramo podatke user-a 
                // zato sto novi Acces Token ima razlicit JTI i mozda nove/razl. claim-ove a stari podaci u Redux mogu biti zastareli
                // Ovo radimo jer refreshToken API ne vraca podatke o user-u
                const userDetailsResponse = await axiosInstance.get('/api/auth/me');
                const userDetails = userDetailsResponse.data;
            
                store.dispatch(loginSuccess(userDetails)); 

                // Resetuj flag i obradi sve zahteve iz reda cekanja
                isRefreshing = false;
                processQueue(null, userDetails);

                console.log("DEBUG: return axiosInstance originalRequset");

                // Pokusavamo originalani request sa novim validnim cookiem
                return axiosInstance(originalRequest);

            } catch (refreshError) {
                // Ako Refresh ne uspe (e.g refresh token istekao ili blacklisted)
                // log out user-a sa frontend-a
                console.log("DEBUG: Catch u responce interseptoru ",refreshError);
                console.error("Token refresh failed, forcing logout:", refreshError);
 
                isRefreshing = false; // Resetuj refresh flag
                processQueue(refreshError, null); // Odbij sve zahteve iz reda čekanja
 
 
 
                store.dispatch(logoutAction());                         // Dispatch logout action to Redux store

                // Pozovemo API da osiguramo server-side invalidation ako treba (refresh failure uglavnom govori da je na serveru vec setovano)
                try {
                    await logoutUser(); // Na serveru da ocistimo
                } catch (logoutApiError) {
                    console.error("Logout API call failed after refresh failure:", logoutApiError);
                }
                

 
                // 
                // Znaci da smo proverili da li je user ulogovan ne bitno da li jeste ili nije
                //ovo nam je vazno da bi Redux znao stanje i da bi isLoading bio gotov !
                store.dispatch(authCheckComplete()); // 


                // KLJUCNO: Hard redirect na login stranicu.
                // Ovo trenutno prekida izvršavanje klijentske aplikacije i sprečava dalja okidanja API poziva.
                // React Router <Navigate> se oslanja na React renderovanje, dok window.location.href odmah preusmerava browser.
                if (window.location.pathname !== '/login') { // Prevent redundant redirect if already on login page
                    window.location.href = '/login';
                }
                
                // Before the hard redirect, ensure the loading state is completed.
                // This will set isLoading to false in Redux before the page navigation.
                console.log("DEBUG: Window location glupost");

                
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
