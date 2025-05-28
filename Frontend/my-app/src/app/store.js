
//za redux 

import {configureStore} from '@reduxjs/toolkit';
import authReducer from './features/authorization/AuthSlice';
/*
reducer je funkcija koja prima trenutno stanje i akciju i vraca novo stanje
- opisuju kako se stanje menja u zavisnosti od akcije
- nikad ne mutatuju state direktno vec returnuju novi copy od state-a
*/

//pravimo redux store i set up-ujemo reducer-a
const store = configureStore({
    reducer: {
        auth: authReducer,          //auth key je slice od state-a  authReducer je nadlezan za taj slice, u globalnom state Tree-u data menagovan od authReducer-a
    },                              //govori Redux-u za auth slice of state koristi authReducer da handlujes promene

});

/*u store-u ce ziveti svi state-ovi npr ovako:
{
  auth: {
    isAuthenticated: false,
    user: null
  },
  // other slices can go here
}

*/

export default store;

