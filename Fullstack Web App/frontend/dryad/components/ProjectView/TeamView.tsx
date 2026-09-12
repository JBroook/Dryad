"use client"

import { Member } from "@/app/home/projects/new/page";
import GlowButton from "../GlowButton";
import { FaPlus, FaRegTrashAlt, FaSearch } from "react-icons/fa";
import { useEffect, useState } from "react";
import { RxCross2 } from "react-icons/rx";
import { IoSearch } from "react-icons/io5";
import { apiFetch } from "@/lib/api";
import { AiOutlineTeam } from "react-icons/ai";
import { IoIosArrowDown } from "react-icons/io";
import { capitalizeFirstLetter } from "@/lib/general";
import { RiVipCrown2Fill } from "react-icons/ri";
import { FiShield } from "react-icons/fi";
import { GoPulse } from "react-icons/go";
import { MdDeleteOutline, MdOutlineEdit, MdRemoveRedEye } from "react-icons/md";
import { BsThreeDots } from "react-icons/bs";
import RoleBadge from "../RoleBadge";

interface TeamViewProps {
    projectID : string | null;
    members : Member[];
    setMembers : (members : Member[])=>void;
}


export default function TeamView(props: TeamViewProps) {
    const [openInviteTab, setOpenInviteTab] = useState<boolean>(false);
    const [searchMember, setSearchMember] = useState<string | null>(null);

    const apiSearchMember = async (nameEmail : string) => {
        await apiFetch(`http://127.0.0.1:8000/api/members/?project=${props.projectID}&search=${nameEmail}`)
        .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
        })
        .then((data)=>props.setMembers(data.map((member : any)=>{
        return {...member, 
            firstName : member.user.first_name, 
            lastName : member.user.last_name,
            email : member.user.email,
            joinDate : member.join_date
        }
        })))
        .catch((err) => console.error("Fetch failed:", err));
    }

    const roleBadge: Record<string, React.ReactElement> = {
        owner : <RoleBadge role="Owner" color="#F59E0B" icon={RiVipCrown2Fill}/>,
        admin : <RoleBadge role="Admin" color="#60A5FA" icon={FiShield}/>,
        manager : <RoleBadge role="Manager" color="#4ADE80" icon={GoPulse}/>,
        viewer : <RoleBadge role="Viewer" color="#94A3B8" icon={MdRemoveRedEye}/>
    }

    
    useEffect(() => {
        if(searchMember===null){
            return;
        }

        const timeout = setTimeout(() => {
            apiSearchMember(searchMember)
        }, 250);

        return () => clearTimeout(timeout);
    }, [searchMember]);

    return (<>
        <div className="flex flex-row justify-between items-center mx-6 mt-6">
            <h1 className="font-semibold text-xl">
                Team Members ({props.members.length})
            </h1>

            <div className="flex flex-row items-center">
                <GlowButton className="btn btn-accent" color="#4ADE80" onClick={()=>setOpenInviteTab(!openInviteTab)}>
                    <FaPlus />
                    Invite Member
                </GlowButton>
            </div>
        </div>

        {openInviteTab && 
            <div className="flex flex-row items-center justify-between mx-6 mt-3 p-4 rounded-xl bg-primary/10 border border-primary/25">
                <IoSearch className="mr-3 text-secondary-content"/>

                <input
                name="email"
                type="email"
                className="input w-full bg-accent/15 flex-1"
                placeholder="colleague@organization.org"
                />

                <button className="btn btn-primary ml-2">
                    Send
                </button>

                <button className="btn btn-secondary text-lg mx-2" onClick={()=>setOpenInviteTab(false)}>
                    <RxCross2/>
                </button>
            </div>}

        <div className="mx-6 mt-2">
            <label className="input bg-secondary w-full border border-white/8 mt-2">
                <IoSearch />
                <input type="search" className="grow" placeholder="Search by name or email..." onChange={(e)=>setSearchMember(e.target.value)} />
            </label>

            <div>
                {props.members.length>0 ?
                    <div className="mb-10">
                    {props.members.map((member, index)=>{
                        
                        return (
                        <div className="bg-base-200 rounded-xl border border-white/8 flex flex-row p-4 mt-5 items-center" key={index}>
                            <div className="avatar">
                                <div className="w-8 rounded-full">
                                    <img src="https://img.daisyui.com/images/profile/demo/yellingcat@192.webp" />
                                </div>
                            </div>
                            <div className="ml-4">
                                <h1 className="font-semibold text-md">
                                    {member.firstName} {member.lastName}
                                    <span>
                                        <details className="dropdown">
                                            {true ?
                                                <summary className="btn m-0 px-0 py-1 h-fit">
                                                    {roleBadge[member.role]}
                                                </summary>
                                                :
                                                <summary className="btn py-0 px-2 h-fit">
                                                    {/* {capitalizeFirstLetter(member.role)} */}
                                                    {/* <IoIosArrowDown /> */}
                                                </summary>
                                            }
                                            <ul className="menu dropdown-content bg-base-300 rounded-box z-1 w-52 p-2 shadow-sm">
                                                <li><a 
                                                    className="text-[#60A5FA]" 
                                                    onClick={()=>{}}>
                                                    Admin
                                                </a></li>
                                                <li><a className="text-[#4ADE80]"
                                                    onClick={()=>{}}>
                                                    Manager
                                                </a></li>
                                                <li><a className="text-[#94A3B8]"
                                                    onClick={()=>{}}>
                                                    Viewer
                                                </a></li>
                                            </ul>
                                        </details>
                                    </span>
                                </h1>
                                <p className="text-secondary-content text-sm">{member.email}</p>
                            </div>
                            <div className="ml-auto flex flex-row items-center">
                                <p className="text-secondary-content text-sm">
                                    Joined {member.joinDate}
                                </p>

                                <details className="dropdown dropdown-left">
                                    <summary className="btn">
                                        <BsThreeDots />
                                    </summary>
                                    <ul className="menu dropdown-content bg-secondary rounded-box z-1 w-52 p-2 mr-2 font-semibold">
                                        <li><a>
                                            <MdOutlineEdit className="text-[#60A5FA] text-xl"/> Change Role
                                        </a></li>
                                        <li><a>
                                            <MdDeleteOutline className="text-error text-lg"/> Remove
                                        </a></li>
                                    </ul>
                                </details>
                            </div>
                        </div>);
                    })}
                    </div>
                :
                    <div className="w-full flex flex-col justify-center items-center text-secondary-content py-10">
                        <AiOutlineTeam className="text-4xl"/>
                        {searchMember==="" ?
                        <>
                            <h1>No team members found</h1>
                            <p className="text-sm">You can invite members by clicking on "Invite Member"</p>
                        </> :
                            <h1>"{searchMember}" couldn't be found</h1>
                        }
                    </div>
                }
            </div>
        </div>
    </>);
}