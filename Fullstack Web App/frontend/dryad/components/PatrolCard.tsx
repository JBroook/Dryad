import getThreatIcon from "@/library/threatIcons";
import { useState } from "react";
import { FaCopy, FaLocationArrow, FaMicrophone, FaPersonRunning, FaRegClock, FaRegUser } from "react-icons/fa6";
import { IoIosArrowDown, IoIosArrowUp } from "react-icons/io";
import { MdOutlineLocationOn, MdRemoveRedEye } from "react-icons/md";
import GlowButton from "./GlowButton";
import { Patrol } from "@/app/home/patrols/page";
import { capitalizeFirstLetter, copyTextToClipboard, timeAgo } from "@/library/general";
import { TbMapRoute } from "react-icons/tb";
import { FiExternalLink } from "react-icons/fi";
import { useRouter } from "next/navigation";
import { RxCross2 } from "react-icons/rx";

interface PatrolCardProps {
    color : string;
    patrol : Patrol
    confirmPatrol : ()=>void;
    dismissPatrol : ()=>void;
    cancelPatrol : ()=>void;
}

export default function PatrolCard(props : PatrolCardProps) {
    const incident = props.patrol.incident;
    const Icon = getThreatIcon(incident.threatClass.name);
    const [isOpen, setIsOpen] = useState(false);
    const assignedDate = new Date(props.patrol.assignedAt);
    const formalAssignedDate = assignedDate.toLocaleString("en-US");
    const timeAgoAssignedDate = timeAgo(props.patrol.assignedAt)

    const timestamp = timeAgo(incident.timestamp)

    // const roleBadge: Record<string, React.ReactElement> = {
    //     owner : <RoleBadge role="Owner" color="#F59E0B" icon={RiVipCrown2Fill}/>,
    //     admin : <RoleBadge role="Admin" color="#60A5FA" icon={FiShield}/>,
    //     manager : <RoleBadge role="Manager" color="#4ADE80" icon={GoPulse}/>,
    //     viewer : <RoleBadge role="Viewer" color="#94A3B8" icon={MdRemoveRedEye}/>
    // }

    const getSeverityColor = (confidence: number) => {
        if (confidence >= 80) return "#d73027"; // very high
        if (confidence >= 60) return "#fc8d59"; // high
        if (confidence >= 40) return "#fee08b"; // medium
        if (confidence >= 20) return "#d9ef8b"; // low
        return "#91cf60";                  // very low
    };

    const color = getSeverityColor(incident.confidence);

    const router = useRouter();

    const openGoogleMaps = (lat : number, lng : number) => {
        window.open(
        `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`,
        "_blank"
        );
    };

    return (
    <div className="collapse rounded-2xl w-full border border-2 border-white/5 px-2 bg-base-200 mb-4">
        <input 
        type="checkbox" 
        className="p-0"
        checked={isOpen}
        onChange={(e) => setIsOpen(e.target.checked)}/>

        <div className="collapse-title flex flex-row items-center pr-4">
            <div className="h-full min-h-12 w-1 rounded-xs ml-2 my-1" style={{backgroundColor : color}} />

            <div className="p-3 rounded-xl border ml-4" style={{backgroundColor : `${color}1A`, borderColor : `${color}1A`}}> 
                {/* 1A appended to give 10% opacity */}
                <Icon className="text-xl" style={{color : color}}/>
            </div>

            <div className="ml-4">
                <div className="flex flex-row mb-1">
                    <h1 className="font-semibold">{incident.threatClass.name} Activity</h1>
                </div>

                <div className="flex flex-row items-center text-secondary-content text-sm">
                    <MdOutlineLocationOn className="mr-1"/> 
                    <p className="mr-3">{`${incident.coordinates.lat?.toPrecision(5)}°, ${incident.coordinates.lng?.toPrecision(5)}°`}</p>

                    <FaRegClock className="mr-1"/> 
                    <p className="mr-3">{timestamp}</p>

                    <p>Project: {props.patrol.project.name}</p>
                </div>
            </div>

            <div className="ml-auto flex flex-row items-center">
                {isOpen ?
                    <IoIosArrowUp className="text-2xl text-secondary-content ml-4" />
                    :
                    <IoIosArrowDown className="text-2xl text-secondary-content ml-4" />
                }
            </div>
        </div>

        <div className="collapse-content w-full">
            <div className="w-full flex">
                <div className="flex-1 bg-base-300 rounded-xl p-4 mr-2">
                    <div className="flex gap-2 items-center">
                        <FaRegUser className="text-xs"/> <p className="text-secondary-content text-sm">Assigned By</p>
                    </div>
                    <h1 className="font-semibold mt-1">
                        {props.patrol.assignedBy.firstName} {props.patrol.assignedBy.lastName}
                    </h1>
                    <p className="text-sm text-secondary-content mt-1">
                        {capitalizeFirstLetter(props.patrol.assignedBy.role)}
                    </p>
                </div>

                <div className="flex-1 bg-secondary rounded-xl p-4 mr-2">
                    <div className="flex gap-2 items-center">
                        <FaRegClock className="text-xs"/> <p className="text-secondary-content text-sm">Assigned At</p>
                    </div>
                    <h1 className="font-semibold mt-1">
                        {formalAssignedDate}
                    </h1>
                    <p className="text-sm text-secondary-content mt-1">
                        {timeAgoAssignedDate}
                    </p>
                </div>

                <div className="flex-1 bg-secondary rounded-xl p-4 mr-2">
                    <div className="flex gap-2 items-center">
                        <MdOutlineLocationOn className="text-xs"/> <p className="text-secondary-content text-sm">GPS Coordinates</p>
                    </div>
                    <h1 className="font-semibold mt-1">
                        {`${incident.coordinates.lat?.toPrecision(5)}°, ${incident.coordinates.lng?.toPrecision(5)}°`}
                    </h1>
                    <button className="btn btn-xs mt-1" 
                    onClick={()=>copyTextToClipboard(`${incident.coordinates.lat?.toPrecision(5)}°, ${incident.coordinates.lng?.toPrecision(5)}°`)}>
                        <FaCopy />
                        Copy
                    </button>
                </div>

                <div className="flex-1 bg-secondary rounded-xl p-4">
                    <div className="flex gap-2 items-center">
                        <FaMicrophone className="text-xs"/> <p className="text-secondary-content text-sm">Detected By</p>
                    </div>
                    
                    <h1 className="font-semibold mt-1">
                        {incident.device.name}
                    </h1>
                    <p className="text-accent text-sm mt-1">
                        {incident.confidence}% Confidence
                    </p>
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

            <div className="flex mt-2 justify-between">
                <div className="flex gap-2">
                    <GlowButton className="btn btn-secondary" color="#4ADE80"
                    onClick={()=>router.push(`/home/project?pid=${props.patrol.project.id}&tab=forest_map&lat=${
                        incident.coordinates.lng
                    }&lng=${
                        incident.coordinates.lat
                    }`)}>
                        <TbMapRoute/>
                        View on Map
                    </GlowButton>
                    

                    <GlowButton className="btn btn-secondary" color="#60A5FA"
                    onClick={()=>openGoogleMaps(incident.coordinates.lng, incident.coordinates.lat)}>
                        <FaLocationArrow />
                        Navigate
                        <FiExternalLink />
                    </GlowButton>
                </div>

                <div className="flex gap-2">
                    {props.patrol.status==="pending" &&
                        <>
                        <GlowButton color="#94A3B8" onClick={props.cancelPatrol}>
                            <RxCross2/>
                            Cancel
                        </GlowButton>

                        <GlowButton color="#4ADE80" onClick={props.confirmPatrol}>
                            Confirm
                        </GlowButton>

                        <GlowButton color="#ef4444" onClick={props.dismissPatrol}>
                            Dismiss
                        </GlowButton>
                        </>
                    }
                </div>

                
            </div>
        </div>
    </div>);
}