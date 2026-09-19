import getThreatIcon from "@/lib/threatIcons";
import { useState } from "react";
import { FaPersonRunning, FaRegClock } from "react-icons/fa6";
import { IoIosArrowDown, IoIosArrowUp } from "react-icons/io";
import { MdOutlineLocationOn } from "react-icons/md";
import GlowButton from "./GlowButton";
import { Patrol } from "@/app/home/patrols/page";

interface PatrolCardProps {
    color : string;
    patrol : Patrol
    confirmIncident : ()=>void;
    dismissIncident : ()=>void;
    assignPatrol : ()=>void;
}

export default function PatrolCard(props : PatrolCardProps) {
    const incident = props.patrol.incident;
    const Icon = getThreatIcon(incident.threatClass.name);
    const [isOpen, setIsOpen] = useState(false);
    const date = new Date(incident.timestamp);

    const casualDate = date.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
    });

    const formalDateTime = date.toLocaleString("en-US");

    return (
    <div className="collapse rounded-2xl w-full border border-2 border-white/5 px-2 bg-base-200 mb-4">
        <input 
        type="checkbox" 
        className="p-0"
        checked={isOpen}
        onChange={(e) => setIsOpen(e.target.checked)}/>

        <div className="collapse-title flex flex-row items-center pr-4">
            <div className="h-full min-h-12 w-1 rounded-xs ml-2 my-1" style={{backgroundColor : props.color}} />

            <div className="p-3 rounded-xl border ml-4" style={{backgroundColor : `${props.color}1A`, borderColor : `${props.color}1A`}}> 
                {/* 1A appended to give 10% opacity */}
                <Icon className="text-xl" style={{color : props.color}}/>
            </div>

            <div className="ml-4">
                <div className="flex flex-row mb-1">
                    <h1 className="font-semibold">{incident.threatClass.name}</h1>
                </div>

                <div className="flex flex-row items-center text-secondary-content text-sm">
                    <MdOutlineLocationOn className="mr-1"/> 
                    <p className="mr-3">{`${incident.coordinates.lat?.toPrecision(5)}°, ${incident.coordinates.lng?.toPrecision(5)}°`}</p>

                    <FaRegClock className="mr-1"/> 
                    <p className="mr-3">{casualDate}</p>

                    <p>Device: {incident.device.name}</p>
                </div>
            </div>

            <div className="ml-auto flex flex-row items-center">
                <div className="flex flex-col items-end">
                    <h1 className="font-semibold text-2xl text-accent">
                        {incident.confidence}%
                    </h1>
                    <p className="text-secondary-content text-sm">confidence</p>
                </div>

                {isOpen ?
                    <IoIosArrowUp className="text-2xl text-secondary-content ml-4" />
                    :
                    <IoIosArrowDown className="text-2xl text-secondary-content ml-4" />
                }
            </div>
        </div>

        <div className="collapse-content w-full">
            <div className="w-full flex">
                <div className="flex-1 bg-secondary rounded-xl p-4 mr-2">
                    <p className="text-secondary-content text-sm mb-2">GPS Coordinates</p>
                    <h1>
                        {`${incident.coordinates.lat?.toPrecision(5)}°, ${incident.coordinates.lng?.toPrecision(5)}°`}
                    </h1>
                </div>

                <div className="flex-1 bg-secondary rounded-xl p-4 ml-2">
                    <p className="text-secondary-content text-sm mb-2">Exact Timestamp</p>
                    <h1>
                        {formalDateTime}
                    </h1>
                </div>
            </div>

            <div className="w-full flex justify-between mt-4">
                <p className="text-secondary-content text-sm">
                    Confidence
                </p>
                <p className="text-accent text-sm">
                    {incident.confidence}%
                </p>
            </div>

            <progress className="progress progress-primary w-full mt-2" value={incident.confidence} max="100"></progress>

            <div className="flex mt-2 gap-2">
                {incident.status=="unconfirmed" &&
                    <>
                    <GlowButton color="#4ADE80" className="btn btn-primary" onClick={props.confirmIncident}>
                        Confirm
                    </GlowButton>

                    <GlowButton color="#ef4444" className="btn btn-error" onClick={props.dismissIncident}>
                        Dismiss
                    </GlowButton>

                    <GlowButton color="#60A5FA" className="btn btn-info" onClick={props.assignPatrol}>
                        <FaPersonRunning />
                        Assign Patrol
                    </GlowButton>   
                    </>
                }

                <button className="btn btn-secondary">
                    View on Map
                </button>
            </div>
        </div>
    </div>);
}