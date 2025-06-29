
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
        console.log("DEBUG INTERCEPTOR: Start of response processing for URL:", originalRequest.url);

        // 1. KLJUČNO: Prvo uhvati našu prilagođenu AuthError koju baca refreshToken().
        // Ovo je najviši prioritet za rukovanje neuspešnim osvežavanjem tokena.


        //pogledaj u notepad-u zasto treba ovaj prvi if

        if (error instanceof AuthError && error.message === "Failed to refresh token") {
            console.error("DEBUG INTERCEPTOR: Custom AuthError from refreshToken catched. Forcing Logout and Re-routing to login page", error);

            isRefreshing = false;                   // Reset refresh flag
            processQueue(error, null);              // Reject all queued requests

            store.dispatch(logoutAction());         // Dispatch Redux logout action
            try { 
                await logoutUser();                 // Attempt server-side invalidation
            } catch (apiLogoutError) { 
                console.error("Logout API call didnt happen after failed refresh-a (expected for Unauthentificated):", apiLogoutError); 
            }
            
            if (window.location.pathname !== '/login') { 
                window.location.href = '/login';     // HARD REDIRECT
            }
            return Promise.reject(error);
   
        }


        // 2. Izuzmi login i register rute iz ove logike interceptora (ako nisu AuthError)
        if (originalRequest.url === '/api/auth/login' || originalRequest.url === '/api/auth/register') { 
            console.log("DEBUG INTERCEPTOR: Login/Register URL, preskačem refresh logiku.");
            return Promise.reject(error);
        }



        // 3. Opšte rukovanje 401 za SVE ostale zahteve (uključujući /api/auth/me)
        // i koji nisu već retry-ovani. OVO JE MESTO GDE SE REFRESH AKTIVIRA.
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            console.log("DEBUG INTERCEPTOR: Caught 401 for protected request:", originalRequest.url, ". Attempting token refresh.");
            
            originalRequest._retry = true; // Označi da je pokušano (za ovaj specifičan zahtev)

            // Debounce: Ako je refresh već u toku, dodaj zahtev u red čekanja
            if (isRefreshing) {
                console.log("DEBUG INTERCEPTOR: Refresh is already in progress, queuing request.");
                return new Promise(function(resolve, reject) {
                    failedQueue.push({ resolve, reject });
                }).then(() => axiosInstance(originalRequest)).catch(err => Promise.reject(err));
            }

            isRefreshing = true; // Postavi flag: refresh je u toku

            try {
                console.log("DEBUG INTERCEPTOR: Calling refreshToken()...");
                await refreshToken(); // Ovaj poziv će baciti AuthError ako refresh propadne
                console.log("DEBUG INTERCEPTOR: refreshToken() succeeded.");
                
                // Ako je refresh uspešan, ažuriraj detalje korisnika i ponovi originalni zahtev
                const userDetailsResponse = await axiosInstance.get('/api/auth/me'); // Proveri /api/ prefiks
                const userDetails = userDetailsResponse.data;
                store.dispatch(loginSuccess(userDetails)); 
                console.log("DEBUG INTERCEPTOR: User details updated, re-attempting original request.");

                isRefreshing = false;
                processQueue(null, userDetails);
                return axiosInstance(originalRequest); // Ponovi originalni zahtev

            } catch (innerError) {
                // Ovaj catch blok će uhvatiti BILO KOJU grešku iz `await refreshToken()`,
                // uključujući i našu `AuthError` (koju će onda obraditi prvi `if` blok na vrhu).
                console.error("DEBUG INTERCEPTOR: Greška pri osvežavanju tokena (uhvaćena u inner catch):", innerError);

                isRefreshing = false;
                processQueue(innerError, null);

                store.dispatch(logoutAction());
                //await logoutUser pravi beskonacnu petlju 
                // try { 
                //     await logoutUser(); 
                // } catch (apiLogoutError) { 
                //     console.error("Logout API call failed after refresh failure (expected for unauthenticated):", apiLogoutError); 
                // }
                
                // Važno: Ovu grešku propagiramo, a `AuthError` handler na vrhu će uraditi redirect.
                return Promise.reject(innerError); 
            }
        }

        
        // 4. Za sve ostale greške (koje nisu 401, ili su već retry-ovane), samo ih propagiraj
        console.log("DEBUG INTERCEPTOR: Greška nije 401 (za zaštićene) ili je već retry-ovana. Propagiram originalnu grešku.", error);
        return Promise.reject(error); // Za sve ostale greške, samo ih re-throw-uj

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
