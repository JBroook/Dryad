import Link from "next/link";
import { FaArrowLeft, FaArrowRight, FaPlus, FaRegTrashAlt } from "react-icons/fa";
import BottomBar from "./BottomBar";
import { RiVipCrown2Fill } from "react-icons/ri";
import { FiShield } from "react-icons/fi";
import { GoPulse } from "react-icons/go";
import { MdRemoveRedEye } from "react-icons/md";
import { AiOutlineTeam } from "react-icons/ai";
import { useState } from "react";
import { BsThreeDots } from "react-icons/bs";
import { IoIosArrowDown } from "react-icons/io";
import { RxCross2 } from "react-icons/rx";
import { apiFetch } from "@/lib/api";
import { Member } from "@/app/home/projects/new/page";

interface StepPageProps {
    submitEvent : () => void;
    backEvent : () => void;
    membersArray : Member[];
    membersFunction : (newMembers : Member[]) => void;
    roleFunction : (index: number, newRole : string) => void;
}

export default function StepFourPage(props: StepPageProps) {
    const infoCards = [
        {title : "Admin", description : "Can manage devices, members and AI models", color : "#60A5FA", icon : FiShield},
        {title : "Manager", description : "Can view incidents and assign patrols", color : "#4ADE80", icon : GoPulse},
        {title : "Viewer", description : "Can receive patrols and confirm incidents", color : "#94A3B8", icon : MdRemoveRedEye},
    ]

    const addMember: React.SubmitEventHandler<HTMLFormElement> = async (e) => {
        e.preventDefault();

        const formData = new FormData(e.currentTarget);
        const email = formData.get("email")

        if(email && email.toString().length>0){
            apiFetch(`http://127.0.0.1:8000/api/users/?email=${email}`)
            .then(async (res) => {
                if (!res.ok) throw new Error(await res.text());
                return res.json();
            })
            .then((data)=>{
                if(data.length>0){
                    const newMember : Member = {
                        id : data[0].id,
                        firstName : data[0].first_name,
                        lastName : data[0].last_name,
                        email : data[0].email,
                        role : "Viewer"
                    }
                    props.membersFunction([...props.membersArray, newMember])
                }else{
                    alert("No user with this email address exists");
                }
            })
            .catch((err) => console.error("Fetch failed:", err));
        }else{
            alert("Please enter a valid email address");
        }

        // if(!res.ok){
        //     alert("Invalid Credentials");
        //     return;
        // }
    }

    const removeMember = (index : number) => {
        props.membersFunction(props.membersArray.filter((_, i) => i !== index));
    }

    return (
    <div className="h-[calc(100vh-5rem)] flex flex-col">
        <div className="flex flex-row ml-30 mt-8">
          <p className="text-sm text-secondary-content">Step 4 of 5</p>
          <p className="text-sm text-accent ml-5 font-semibold">Team</p>
        </div>

        <h1 className="pt-3 text-3xl font-bold mx-30">Build Your Team</h1>
        <p className="pt-2 text-secondary-content mx-30">Invite colleagues to help monitor and respond to incidents.</p>

        <div className="mx-30 flex-1">
            <div className="bg-base-300 rounded-xl border border-accent/50 mt-8 flex flex-row px-4 py-5">
                <RiVipCrown2Fill className="text-accent text-xl mr-4"/>
                <p className="text-accent text-sm">You will automatically be added as the <b>Owner</b> of this project with full administrative access.</p>
            </div>

            <form className="pt-6" onSubmit={addMember}>
                <fieldset className="fieldset">
                    <legend className="fieldset-legend font-medium text-secondary-content">Invite Team Members</legend>
                    <div className="flex flex-row">
                        <input
                        name="email"
                        type="email"
                        className="input w-full bg-base-200 border flex-1"
                        placeholder="colleague@organization.org"
                        />

                        <button className="btn btn-primary ml-2">
                            <FaPlus />
                            Add
                        </button>
                    </div>
                </fieldset>
            </form>

            <div className="w-full grid grid-cols-3 gap-6 mt-5">
                {infoCards.map((card, index)=>{
                    const Icon = card.icon;
                    return <div className="p-4 bg-base-200 rounded-xl border border-white/8" key={index}>
                        <div className="flex flex-row items-center mb-2">
                            <Icon className="mr-2" style={{color : card.color}}/>
                            <h1 className="font-semibold"  style={{color : card.color}}>{card.title}</h1>
                        </div>
                        <p className="text-sm text-secondary-content">
                            {card.description}
                        </p>
                    </div>})}
            </div>

            {props.membersArray.length>0 ?
                <div className="mb-10">
                {props.membersArray.map((member, index)=>{
                    return (
                    <div className="bg-secondary rounded-xl border border-white/8 flex flex-row p-4 mt-5 items-center" key={index}>
                        <div className="avatar">
                            <div className="w-8 rounded-full">
                                <img src="https://img.daisyui.com/images/profile/demo/yellingcat@192.webp" />
                            </div>
                        </div>
                        <div className="ml-4">
                            <h1 className="font-semibold text-md">{member.firstName} {member.lastName}</h1>
                            <p className="text-secondary-content text-sm">{member.email}</p>
                        </div>
                        <div className="ml-auto flex flex-row items-center">
                            <details className="dropdown mr-2">
                                <summary className="btn m-1">
                                    <IoIosArrowDown />
                                    {member.role}
                                </summary>
                                <ul className="menu dropdown-content bg-base-300 rounded-box z-1 w-52 p-2 shadow-sm">
                                    <li><a 
                                        className="text-[#60A5FA]" 
                                        onClick={()=>props.roleFunction(index, "Admin")}>
                                        Admin
                                    </a></li>
                                    <li><a className="text-[#4ADE80]"
                                        onClick={()=>props.roleFunction(index, "Analyst")}>
                                        Analyst
                                    </a></li>
                                    <li><a className="text-[#94A3B8]"
                                        onClick={()=>props.roleFunction(index, "Viewer")}>
                                        Viewer
                                    </a></li>
                                </ul>
                            </details>

                            <button 
                                className="btn btn-ghost text-error text-lg px-1"
                                onClick={()=>removeMember(index)}>
                                <FaRegTrashAlt />
                            </button>
                        </div>
                    </div>);
                })}
                </div>
            :
                <div className="w-full flex flex-col justify-center items-center text-secondary-content py-20">
                    <AiOutlineTeam className="text-4xl"/>
                    <h1>No team members added yet</h1>
                    <p className="text-xs">You can also invite members after creating the project</p>
                </div>
            }
        </div>

        <BottomBar next="Continue" back="Cancel" formID="project-form" backEvent={props.backEvent}/>
    </div>);
}