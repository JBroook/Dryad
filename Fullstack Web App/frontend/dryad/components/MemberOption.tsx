import { Member } from "@/app/home/projects/new/page";
import { RiVipCrown2Fill } from "react-icons/ri";
import { MdRemoveRedEye } from "react-icons/md";
import { FiShield } from "react-icons/fi";
import { GoPulse } from "react-icons/go";
import RoleBadge from "./RoleBadge";
import { IoMdCheckmark } from "react-icons/io";

interface MemberOptionProps {
    member : Member;
    addMember : ()=>void;
    selected : boolean;
}

export default function MemberOption(props : MemberOptionProps) {
    const roleBadge: Record<string, React.ReactElement> = {
        owner : <RoleBadge role="Owner" color="#F59E0B" icon={RiVipCrown2Fill}/>,
        admin : <RoleBadge role="Admin" color="#60A5FA" icon={FiShield}/>,
        manager : <RoleBadge role="Manager" color="#4ADE80" icon={GoPulse}/>,
        viewer : <RoleBadge role="Viewer" color="#94A3B8" icon={MdRemoveRedEye}/>
    }

    return (<div className={`rounded-xl p-4 flex mb-2 cursor-pointer items-center ${props.selected ? 
        "bg-base-300 border border-accent/25" 
        : 
        "bg-secondary"}`}
                onClick={props.addMember}>
        <div className="avatar">
            <div className="w-8 rounded-full">
                <img src="https://img.daisyui.com/images/profile/demo/yellingcat@192.webp" />
            </div>
        </div>

        <div className="ml-4">
            <div className="flex">
                <h1 className="font-semibold text-base">
                    {props.member.firstName} {props.member.lastName}
                </h1>
                {roleBadge[props.member.role]}
            </div>
            <p className="text-secondary-content text-sm">{props.member.email}</p>
        </div>

        {props.selected &&
        <div className="rounded-full bg-accent text-white text-xl p-1 h-fit ml-auto">
            <IoMdCheckmark />
        </div>}
    </div>);
}