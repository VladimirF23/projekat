import axiosInstance  from "./axiosInstance";


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
        if (error.response && error.response.data && error.response.data.error) {
            throw error.response.data.error;
        } else {
            throw "An unexpected error occurred during logout.";
        }
    }

};

//ovo ce zvati Axios interceptor kada Access token expire-ruje
export const refreshToken = async() =>{
    try{
        // Flask-ov /auth/refresh je POST request treba mu validan refresh token cookie
        // i trebace mu validan CSRF token iz JS readable cookie-a
        const response = await axiosInstance.post('/api/auth/refresh');
        return response.data;       //dobicemo samo poruku da su postavljeni novi cookie

    }catch(error)
    {
        if (error.response && error.response.data && error.response.data.error) {
            throw error.response.data.error;
        } else {
            throw "An unexpected error occurred during token refresh.";
        }

    }

};