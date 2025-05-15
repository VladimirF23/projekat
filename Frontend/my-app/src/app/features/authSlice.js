import { createSlice } from "@reduxjs/toolkit";

//inicijalno stanje za auth slice, user cuva user data
const initialState = {
    isAuthenticated: false,
    user: null,
};

//authSlice definise kako state izgleda i kako se moze updejtovati, inicijalizujemo initialState, reduceri ->modifikuju state
const authSlice = createSlice({
    name:'auth',
    initialState,
    reducers: {
        login:(state,action) =>{
            state.isAuthenticated = true;
            state.user = action.payload;
        },
        logout:(state) =>{
            state.isAuthenticated = false;
            state.user = null
        },
    },
});

export const {login,logout} = authSlice.actions;            //exportuje action creator-s (login i loggout) za koriscenje u components da bi se discpatch-ovale ove akcije
export default authSlice.reducer;                           // funkcija koju Redux zove da updejtuje state