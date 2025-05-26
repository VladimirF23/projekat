import axiosInstance  from "./axiosInstance";


//ova funkcija ce zvati API login e
export const loginUser = async(credentials) =>{
    try{
        //post request, preko axiosa gadja API backend 
        const response = await axiosInstance.post('/auth/login',credentials);

        //ako je uspsesan,returnujemo response data
        return response.data
    }catch(error){
        //catchujem error posto mi API vraca error a ne message
        
        if (error.response && error.response.data && error.response.data.error) {
            throw error.response.data.error;
        }else{
            throw "An unexpected error occurred.";
        }
    }

};