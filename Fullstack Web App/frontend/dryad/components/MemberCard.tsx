import { Member } from "@/app/home/projects/new/page";
import { BsThreeDots } from "react-icons/bs";
import { FiShield } from "react-icons/fi";
import { GoPulse } from "react-icons/go";
import { MdDeleteOutline, MdOutlineEdit, MdRemoveRedEye } from "react-icons/md";
import { RiVipCrown2Fill } from "react-icons/ri";
import RoleBadge from "./RoleBadge";
import { IoIosArrowDown } from "react-icons/io";
import { capitalizeFirstLetter } from "@/lib/general";
import { useState } from "react";
import { RxCross2 } from "react-icons/rx";

interface MemberCardProps {
    member : Member;
    changeMemberRole : (id : number, newRole : string) => void;
    removeModal : () => void;
}

export default function MemberCard(props : MemberCardProps) {
    const [isEditing, setIsEditing] = useState<boolean>(false);
    
    const roleBadge: Record<string, React.ReactElement> = {
        owner : <RoleBadge role="Owner" color="#F59E0B" icon={RiVipCrown2Fill}/>,
        admin : <RoleBadge role="Admin" color="#60A5FA" icon={FiShield}/>,
        manager : <RoleBadge role="Manager" color="#4ADE80" icon={GoPulse}/>,
        viewer : <RoleBadge role="Viewer" color="#94A3B8" icon={MdRemoveRedEye}/>
    }

    const setNewRole = (role : string) => {
        setIsEditing(false);
        props.changeMemberRole(props.member.id, role)
    }

    return (
    <div className="bg-base-200 rounded-xl border border-white/8 flex flex-row p-4 mt-5 items-center">
        <div className="avatar">
            <div className="w-8 rounded-full">
                <img src="https://img.daisyui.com/images/profile/demo/yellingcat@192.webp" />
            </div>
        </div>
        <div className="ml-4">
            <div className="flex items-center">
                <h1 className="font-semibold text-md">{props.member.firstName} {props.member.lastName}</h1>
                {!isEditing ?
                roleBadge[props.member.role]
                :
                <details className="dropdown">
                    <summary className="btn py-0 px-2 h-fit">
                        {capitalizeFirstLetter(props.member.role)}
                        <IoIosArrowDown />
                    </summary>
                    <ul className="menu dropdown-content bg-base-300 rounded-box z-1 w-52 p-2 shadow-sm">
                        <li><a 
                            className="text-[#60A5FA]" 
                            onClick={()=>setNewRole("admin")}>
                            Admin
                        </a></li>
                        <li><a className="text-[#4ADE80]"
                            onClick={()=>setNewRole("manager")}>
                            Manager
                        </a></li>
                        <li><a className="text-[#94A3B8]"
                            onClick={()=>setNewRole("viewer")}>
                            Viewer
                        </a></li>
                    </ul>
                </details>
                }
            </div>
            <p className="text-secondary-content text-sm">{props.member.email}</p>
        </div>
        <div className="ml-auto flex flex-row items-center">
            <p className="text-secondary-content text-sm">
                Joined {props.member.joinDate}
            </p>

            <details className="dropdown dropdown-left">
                <summary className="btn mx-2">
                    <BsThreeDots />
                </summary>
                <ul className="menu dropdown-content bg-secondary rounded-box z-1 w-52 p-2 mr-2 font-semibold">
                    <li><a onClick={()=>setIsEditing(!isEditing)}>
                        {isEditing?
                            <><RxCross2 className="text-xl"/> Cancel Edit</>
                            :
                            <><MdOutlineEdit className="text-[#60A5FA] text-xl"/> Change Role</>
                        }
                    </a></li>
                    <li><a onClick={props.removeModal}>
                        <MdDeleteOutline className="text-error text-lg"/> Remove
                    </a></li>
                </ul>
            </details>
        </div>
    </div>);
}