//login forma, handluje submisiion od user-a, dispatchuje login action i menaguje error-e
//updejtuje redux store

import React, {useState} from "react";
import { useDispatch, useSelector } from "react-redux";
import { loginUser } from "../../api/authApi";

//Reduceri za redux store state
import { loginSuccess,loginFailure } from "./AuthSlice";

//da bi axios-os mogao da salje u header-u token user-a ako je logovan uspesno
import { setAuthTokenAxios } from '../../api/axiosInstance';

//znaci posle uspesno logovanje zovemo setAuthTokenAxios(token) da bi axios mogao API-ima u headeru da salje token
//i takodje u localstorage-u tj reduxu cuvamo JWT token radi reloadova itd, localStorage.setItem('token', data.access_token);


const Login = () =>{
    const [username,setUsername] = useState('');
    const [password,setPassword] =  useState('');

    //pristupimo error-u preko Redux state-a
    /*
        const initialState = {
            isAuthenticated: false,
            user: null,
            error:null
        };

        ovaj state definise authSlice i on ga modifikuje
    */
    const error = useSelector((state) => state.auth.error)
    
    //inicijalizujemo redux dispatch
    const dispatch = useDispatch()


    //handlujemo submit logina
    const handleSubmit = async(e) =>{
        e.preventDefault();                 //preventujemo page reload
        try{
            const credentials = {username,password};

            //calujemo login AXIOS-a koji salje API-u 
            const data = await loginUser(credentials)

            //store-ujemo  JWT token u local-storage-u, ovo je 
            localStorage.setItem('token',data.access_token)
            
        }catch(err){

            //mi dispatchujemo ovo, redux salje action ka reducer-u loginFailiure (AuthSlice), reducer kalkulise nove stanje i akciju, store save-uje novo stanje
            //UI componente slusaju store i updejtuju sami sebe na osnovu novog state-a
            dispatch(loginFailure(err));
        }
    }


}
