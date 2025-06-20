
// /authApi.js

import axiosInstance  from "./axiosInstance";
import  refreshAxiosInstance  from "./axiosInstance";
import AuthError  from "../utils/AuthError";
//ova funkcija ce zvati API login e
export const loginUser = async(credentials) =>{
    try{
        //post request, preko axiosa nginx ce proslediti na moj pravi API, api ovde je za nginx i on ce skinuti /api/ 
        const response = await axiosInstance.post('/api/auth/login',credentials);

        return response.data        // Flask vraca {"message": "User logged in successfully"}
    }catch(error){
        //catchujem error posto mi API vraca error a ne message
        
        if (error.response && error.response.data && error.response.data.error) {
            throw error.response.data.error;
        }else{
            throw "An unexpected error occurred.";
        }
    }
};

export const logoutUser = async() =>{
    try{
        const response = await axiosInstance.post('/api/auth/logout');
        return response.data;
    }catch(error){
        console.error("DEBUG authApi: logoutUser failed:", error.response?.data || error.message);
        throw error; //  Ovo osigurava da interceptor's catch blok uhvati gresku

    }

};

//ovo ce zvati Axios interceptor kada Access token expire-ruje
export const refreshToken = async() =>{

    console.log("DEBUG AUTHAPI: Trying to refresh token. Using refreshAxiosInstance."); // Dodato logovanje

    try{
        // Flask-ov /auth/refresh je POST request treba mu validan refresh token cookie
        // i trebace mu validan CSRF token iz JS readable cookie-a

        console.log("DEBUG AUTHAPI: Sending POST to /api/auth/refresh..."); // Dodato logovanje


        //preko refresh AxiosInstance-a posto on nema prikljucene interceptore
        const response = await refreshAxiosInstance.post('/api/auth/refresh',{},{withCredentials:true});


        console.log("DEBUG AUTHAPI: Successfully received refresh response:", response.data); // Dodato logovanje

        return response.data;       //dobicemo samo poruku da su postavljeni novi cookie

    }catch(error)
    {
        // // Kljucno: Logujem grešku i OBAVEZNO JE BACI PONOVO (re-throw)
        // console.error("DEBUG authApi: refreshToken failed:", error.response?.data || error.message);     
        // throw error; //  Osigurava da interceptor's catch blok uhvati grešku !!!!


        // KLJUČNO: Loguj grešku i OBAVEZNO BACI NOVU AuthError grešku
        // Ovaj log bi se MORAO pojaviti ako Axios uhvati grešku
        console.error("DEBUG AUTHAPI: refreshToken caught error:", error.response?.data || error.message || error); 
        console.error("DEBUG AUTHAPI: Error object details:", error); // Loguj ceo error objekat
        throw new AuthError("Failed to refresh token", error.response?.status);
    
    }

};