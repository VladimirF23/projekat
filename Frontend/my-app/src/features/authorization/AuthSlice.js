import { createSlice } from "@reduxjs/toolkit";

//inicijalno stanje za auth slice, user cuva user data
const initialState = {
    isAuthenticated: false,
    user: null,
    error:null
};

//authSlice definise kako state izgleda i kako se moze updejtovati, inicijalizujemo initialState, reduceri ->modifikuju state
const authSlice = createSlice({
    name:'auth',
    initialState,
    reducers: {
        loginSuccess:(state,action) =>{
            state.isAuthenticated = true;
            state.user = action.payload;
            state.error= null;
        },
        logout:(state) =>{
            state.isAuthenticated = false;
            state.user = null;
            state.error=null;
        },
        loginFailure: (state,action) =>{
            state.isAuthenticated=false;
            state.user= null;
            state.error = action.payload;

        },
    },
});

export const {loginSuccess,loginFailure,logout} = authSlice.actions;            //exportuje action creator-s (loginSuccess... i loggout) za koriscenje u components da bi se discpatch-ovale ove akcije
export default authSlice.reducer;                           // funkcija koju Redux zove da updejtuje state