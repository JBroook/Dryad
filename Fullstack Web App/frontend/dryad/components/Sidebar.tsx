"use client"

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BsTree } from "react-icons/bs";
import { IoSettingsOutline, IoWarningOutline } from "react-icons/io5";
import { TbMapRoute } from "react-icons/tb";
import HollowCard from "./HollowCard";
import { MdOutlineDarkMode, MdOutlineLightMode } from "react-icons/md";
import { useState } from "react";
import { useTheme } from "next-themes";

export default function Sidebar() {
    const sidebarOptions = [
        {href : "/home", name : "Projects", icon: BsTree},
        {href : "/home/incidents", name : "Incidents", icon: IoWarningOutline},
        {href : "/home/patrols", name : "Patrols", icon: TbMapRoute},
        {href : "/home/settings", name : "Settings", icon: IoSettingsOutline},
    ]
    const [mode, setMode] = useState<boolean>(true);
    const pathname = usePathname();
    const {theme, setTheme} = useTheme();
    const changeTheme = () => {
        setMode(!mode)
        setTheme(mode ? "mytheme-light" : "mytheme-dark")
    }

    return (
        <aside className="w-64 h-screen">
            <div className="flex flex-col w-full h-full bg-secondary border-r border-r-white/5 border-r-[2px]">
                <div className="py-5 pl-5 border-b border-b-white/5 border-b-[2px]">
                    <h1 className="text-3xl font-semibold">Dryad</h1>
                </div>

                <ul className="menu p-4 w-full">
                    {sidebarOptions.map((option, index)=>{
                        const Icon = option.icon;
                        const isActive = pathname === option.href;
                        return (<li key={index} className="py-1 bg-secondary">
                        <Link 
                            href={option.href}
                            className={`text-md py-2 font-medium ${isActive ? "bg-[#0C2618] text-accent" : "text-secondary-content"}`}
                        >
                            <Icon className={`text-lg mr-1 ${isActive ? "text-accent" : "text-secondary-content"}`}/>
                            {option.name}
                        </Link>
                        </li>);
                    })}
                </ul>
                
                <div className="flex flex-col items-center mt-auto border-t border-t-[2px] border-t-white/5">
                    <button className="bg-white/8 rounded-xl font-medium mt-3 p-3 w-[90%] flex flex-row justify-start items-center hover:cursor-pointer" 
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
                            <h1 className="font-semibold">Anna Souza</h1>
                            <p className="text-secondary-content text-xs truncate w-40">annasouza@gmail.com</p>
                        </div>
                    </HollowCard>
                    <button className="w-full justify-center my-2 btn btn-link no-underline text-secondary-content hover:text-[#EF4444]">
                        Sign out
                    </button>
                </div>
            </div>
        </aside>
    );
}