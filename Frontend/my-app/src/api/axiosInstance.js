import axios from 'axios'
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
    baseURL: 'http://localhost:5000',                //flask moj
    headers:{
        'Content-Type': 'application/json',          //govori serveru da ce axios slati podatke u JSON formatu
    },
})


//funkcija za set-ovanje tokena posle login-a i register
export const setAuthTokenAxios = (token) =>{
    if (token){                                                                     //ako postoji token (posle login-a i registera imati ) svakom requestu se dodaje  JWT token
        axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        //dodaje se Authorization header svakom requstu i ovako izgleda Authorization: Bearer <Your_JWT_Token>


    }else{
        //ako ne postoji brise se authorization header
        delete axiosInstance.defaults.headers.common['Authorization'];

    }


}

export default axiosInstance;
