import { Device } from "@/app/home/project/page";
import { capitalizeFirstLetter, timeAgo } from "@/lib/general";
import { useState } from "react";
import { BsThreeDots } from "react-icons/bs";
import { FaWifi } from "react-icons/fa6";
import { IoLocationOutline, IoPower } from "react-icons/io5";
import { MdDeleteOutline, MdOutlineEdit } from "react-icons/md";

interface DeviceCardProps {
    device : Device;
    deleteEvent : (index : number)=> void;
    renameDevice : (id : number, newName : string) => void;
    toggleDevice : (id : number) => void;
}

export default function DeviceCard(props : DeviceCardProps) {
    const [isRenaming, setIsRenaming] = useState(false);
    const [newName, setNewName] = useState("");

    const lat = props.device.location.coordinates[1].toFixed(4)
    const lng = props.device.location.coordinates[0].toFixed(4)

    const lastSeenTime = timeAgo(props.device.lastSeen)

    const finishRename = () => {
        if (!isRenaming) return;

        // don't allow empty name
        const trimmed = newName.trim()
        if (!trimmed) {
            setIsRenaming(false);
            return;
        }

        props.renameDevice(props.device.id, trimmed);
        setIsRenaming(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            finishRename();
        }

        if (e.key === "Escape") {
            setIsRenaming(false);
        }
    };

    const handleRename = () => {
        setIsRenaming(true);
        setNewName(props.device.name)
    }
    
    return (
    <div className="py-4 px-6 rounded-xl bg-base-200 border border-white/8" style={{opacity : (props.device.status==="online" ? 1:0.5)}}>
        <div className="flex flex-row justify-between">
            <div className="flex flex-row items-center">
                <FaWifi className={`mr-2 ${props.device.status==="online" ? "text-accent" : "text-secondary-content"}`}/>
                {isRenaming ? (
                <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onBlur={finishRename}
                    onKeyDown={handleKeyDown}
                    className="input input-sm input-bordered font-semibold"
                />
                ) : (<>
                    
                    <h1 className={`font-semibold ${props.device.status==="offline" && "text-secondary-content"}`}>
                        {props.device.name}
                    </h1>
                    </>
                )}
            </div>

            <div className="flex flex-row items-center">
                {props.device.status==="online" ?
                    <div className="badge badge-soft badge-accent font-semibold">Online</div>
                    :
                    <div className="badge badge-soft badge-[#6B7280] font-semibold">Offline</div>
                }

                <details className="dropdown dropdown-left">
                    <summary className="btn p-1"><BsThreeDots/></summary>
                    <ul className="menu dropdown-content bg-secondary rounded-box z-1 w-52 p-2 mr-2">
                        <li><a onClick={()=>props.toggleDevice(props.device.id)}>
                            {props.device.status==="offline" ? 
                                <>
                                    <IoPower className="text-accent text-lg"/>
                                    Set Online
                                </>
                            : 
                                <>
                                    <IoPower className="text-warning text-lg"/>
                                    Set Offline
                                </>}
                        </a></li>
                        <li><a onClick={handleRename}>
                            <MdOutlineEdit className="text-[#60A5FA] text-xl"/> Rename
                        </a></li>
                        <li><a>
                            <IoLocationOutline className="text-[#A78BFA] text-lg"/> Show on Map
                        </a></li>
                        <li><a onClick={()=>props.deleteEvent(props.device.id)}>
                            <MdDeleteOutline className="text-error text-lg"/> Remove
                        </a></li>
                    </ul>
                </details>
            </div>
        </div>

        <div className="flex justify-between items-center text-sm mt-2">
            <p className="text-secondary-content">Battery</p>
            <p className="text-accent">{props.device.battery}%</p>
        </div>

        <progress className="progress progress-primary w-full mt-2" value={80} max="100"></progress>

        <div className="flex justify-between items-center text-sm my-2 text-secondary-content">
            <p>{lat}°, {lng}°</p>
            <p>Last ping {lastSeenTime}</p>
        </div>
    </div>);
}