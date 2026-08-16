import Link from "next/link";
import { FaArrowLeft, FaArrowRight } from "react-icons/fa";
import BottomBar from "./BottomBar";
import { RiVipCrown2Fill } from "react-icons/ri";
import { FiShield } from "react-icons/fi";
import { GoPulse } from "react-icons/go";
import { MdRemoveRedEye } from "react-icons/md";
import { AiOutlineTeam } from "react-icons/ai";

interface StepPageProps {
    submitEvent : () => void;
    backEvent : () => void;
    nameValue : string;
    descriptionValue : string;
    colorValue : string;
    nameFunction : (e : React.ChangeEvent<HTMLInputElement>) => void;
    descriptionFunction : (e : React.ChangeEvent<HTMLTextAreaElement>) => void;
    colorFunction : (e : React.ChangeEvent<HTMLInputElement>) => void;
}

export default function StepFourPage(props: StepPageProps) {
    const infoCards = [
        {title : "Admin", description : "Can manage devices, confirm incidents, invite members", color : "#60A5FA", icon : FiShield},
        {title : "Analyst", description : "Can view all data and confirm incidents", color : "#4ADE80", icon : GoPulse},
        {title : "Viewer", description : "Read-only access to incidents and map", color : "#94A3B8", icon : MdRemoveRedEye},
    ]

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

            <form className="pt-6" onSubmit={props.submitEvent} id="project-form">
                <fieldset className="fieldset">
                    <legend className="fieldset-legend font-medium text-secondary-content">Invite Team Members</legend>
                    <input
                    type="text"
                    className="input w-full bg-base-200 border"
                    placeholder="colleague@organization.org"
                    value={props.nameValue}
                    onChange={props.nameFunction}
                    />
                </fieldset>

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

                <div className="w-full flex flex-col justify-center items-center text-secondary-content py-20">
                    <AiOutlineTeam className="text-4xl"/>
                    <h1>No team members added yet</h1>
                    <p className="text-xs">You can also invite members after creating the project</p>
                </div>
            </form>
        </div>

        <BottomBar next="Continue" back="Cancel" formID="project-form" backEvent={props.backEvent}/>
    </div>);
}