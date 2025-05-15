import { Link } from "react-router-dom";
import {Search, User} from "lucide-react"
import { useSelector, useDispatch } from "react-redux";
import { logout } from "../app/features/authSlice";     //uzimamo logout posto se ovde direktno mozemo loggoutovati ako je user prijavljen
import Login from "../pages/Login";
                                                        //login ce se na drugom mestu desavati posto ce se morati popouniti forma login-a

//search,User su ikonice iz ovog library-a od reacta      

//link za navigaciju izmedju razl URL bez refresh-a aplikacije slizno <a> tagu samo optimizovano za React


/*className je CSS klasa u react-u, bg-> backgroung gre, flex->horizontalno children item-e da stavi, items-center->vertikalno align elemente
justify-between white space mesta izmedju elementa podjednako pushuje left i right part-ove ka edgovima

Reddit_logo sam stavio u public jer nema potrebe onda da se importuje i idealno je za static assete kao sto su logo-i, brze ce se loadovati i globalno je dostupno
alt - text description ako se slucajno ne loaduje logo
*/

const Navbar = () =>{
    //State da pratimo da li je user prijavljen
    const { isAuthenticated, user } = useSelector((state)=>state.auth);
    const dispatch = useDispatch()
    return(
        <nav className="bg-gray-800 text-white p-3 flex items-center justify-between">

        {/* Levo - Logo */}
        <Link to="/" className="text-2xl font-bold flex items-center">
            <img 
                src="/Reddit_Logo.png"
                alt="Reddit Logo"
                className="w-8 h-8 mr-2"
            />
        Reddit
        </Link>

        {/*Centar - Search bar*/}
        <div className="relative w-1/2">
            <input
            type="text"
            placeholder="Search Subbredits, Users, Posts..."
            className="w-full p-2 rounded-lg text-gray-900 focus:outline-none"
            />
            {/*ikonica ucitana iz lucide-react */}
            <Search className="absolute right-3 top-2 text-gray-500"/>
        </div>


        {/*Desno - MyProfile  User je ikonica !*/}

        {/* {}- dozvoljava da ubacimo unutra Jcode, ? ternarni ako je Truee onda imamo MyProfile ako nije onda se renderuje code ispod (:)
        dole se poziva dispatch za logout od reducera- authReducer  */}
        {isAuthenticated ?(
            <div className="flex items-center space-x-4">
                <Link to="/profile" className="flex items-center space-x-2">
                    <User className="text-white"/>      
                    <span>{user?.username || "MyProfile"}</span>
                </Link>
                <button onClick={() =>dispatch(logout())}className="bg-red-500 px-3 py-1 rounded-lg">
                    Loggout
                </button>

            </div>
            ) :(
                <Login to="/login" className="bg-blue-500 px-3 py-1 rounded-lg">
                    Login
                </Login>  
            )
        }
        </nav>
    );

};

export default Navbar;
