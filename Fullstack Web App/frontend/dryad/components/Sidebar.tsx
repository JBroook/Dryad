"use client"

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BsTree } from "react-icons/bs";
import { IoSettingsOutline, IoWarningOutline } from "react-icons/io5";
import { TbMapRoute } from "react-icons/tb";
import HollowCard from "./HollowCard";
import { MdOutlineDarkMode, MdOutlineLightMode } from "react-icons/md";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { apiFetch } from "@/lib/api";

export default function Sidebar() {
    const sidebarOptions = [
        {href : "/home/projects", name : "Projects", icon: BsTree},
        // {href : "/home/incidents", name : "Incidents", icon: IoWarningOutline},
        {href : "/home/patrols", name : "Patrols", icon: TbMapRoute},
        // {href : "/home/settings", name : "Settings", icon: IoSettingsOutline},
    ]
    const [mode, setMode] = useState<boolean>(true);
    const pathname = usePathname();
    const {theme, setTheme} = useTheme();
    const changeTheme = () => {
        setMode(!mode)
        setTheme(mode ? "mytheme-light" : "mytheme-dark")
    }
    const router = useRouter()
    function logout() {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");

        router.push("/login");
    }

    const [firstName, setFirstName] = useState<string>("")
    const [lastName, setLastName] = useState<string>("")
    const [email, setEmail] = useState<string>("")
    
    const setUserInfo = (data : any) => {
        setFirstName(data.first_name);
        setLastName(data.last_name);
        setEmail(data.email);
      }
    
      useEffect(()=>{
        // const token = localStorage.getItem("access");
    
        // if(!token){
        //   router.push("/login")
        // }else{
        //   setAuthenticated(true)
        // }
    
        // fetch user info
        const userID = localStorage.getItem("userID")
        apiFetch(`http://127.0.0.1:8000/api/users/${userID}`)
          .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
          })
          .then(setUserInfo)
          .catch((err) => console.error("Fetch failed:", err));
      }, [])

    return (
        <aside className="w-64 h-screen fixed left-0 top-0">
            <div className="flex flex-col w-full h-full bg-base-200 border-r border-r-base-300 border-r-[2px]">
                <div className="py-5 pl-5 border-b border-b-base-300 border-b-[2px]">
                    <h1 className="text-3xl font-semibold">Dryad</h1>
                </div>

                <ul className="menu p-4 w-full">
                    {sidebarOptions.map((option, index)=>{
                        const Icon = option.icon;
                        const isActive = pathname === option.href;
                        return (<li key={index} className="py-1 bg-base-200">
                        <Link 
                            href={option.href}
                            className={`text-md py-2 font-medium ${isActive ? "bg-base-300 text-accent" : "text-secondary-content"}`}
                        >
                            <Icon className={`text-lg mr-1 ${isActive ? "text-accent" : "text-secondary-content"}`}/>
                            {option.name}
                        </Link>
                        </li>);
                    })}
                </ul>
                
                <div className="flex flex-col items-center mt-auto border-t border-t-[2px] border-t-base-300">
                    <button className="bg-base-100 rounded-xl font-medium mt-3 p-3 w-[90%] flex flex-row justify-start items-center hover:cursor-pointer border border-base-300" 
                    onClick={changeTheme}>
                         {mode ? 
                            <MdOutlineLightMode className="text-secondary-content text-xl mr-3"/>
                            :
                            <MdOutlineDarkMode className="text-secondary-content text-xl mr-3"/>
                         }
                        <h1 className="text-secondary-content text-sm">
                            {mode ? "Light Mode" : "Dark Mode"}
                        </h1>
                    </button>
                    <HollowCard className="mt-3 p-3 w-[90%] flex flex-row">
                        <div className="avatar">
                            <div className="w-8 rounded-full">
                                <img src="https://img.daisyui.com/images/profile/demo/yellingcat@192.webp" />
                            </div>
                        </div>
                        <div className="ml-4">
                            <h1 className="font-semibold">{firstName} {lastName}</h1>
                            <p className="text-secondary-content text-xs truncate w-40">{email}</p>
                        </div>
                    </HollowCard>
                    <button className="w-full justify-center my-2 btn btn-link no-underline text-secondary-content hover:text-[#EF4444]"
                    onClick={logout}>
                        Sign out
                    </button>
                </div>
            </div>
        </aside>
    );
}