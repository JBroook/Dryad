import { Device } from "@/app/home/project/page";
import { BsThreeDots } from "react-icons/bs";
import { FaPen } from "react-icons/fa";
import { FaWifi } from "react-icons/fa6";
import { IoLocationOutline, IoPower } from "react-icons/io5";
import { MdDelete, MdDeleteOutline, MdOutlineEdit } from "react-icons/md";

interface DeviceCardProps {
    device : Device;
    deleteEvent : (index : number)=> void;
}

export default function DeviceCard(props : DeviceCardProps) {
    const lat = props.device.location.coordinates[1].toFixed(4)
    const lng = props.device.location.coordinates[0].toFixed(4)
    return (
    <div className="py-4 px-6 rounded-xl bg-base-200 border border-white/8">
        <div className="flex flex-row justify-between">
            <div className="flex flex-row items-center">
                <FaWifi className="mr-2 text-accent"/>
                <h1 className="font-semibold">{props.device.name}</h1>
            </div>

            <div className="flex flex-row items-center">
                <div className="badge badge-soft badge-accent font-semibold">Online</div>

                <details className="dropdown">
                    <summary className="btn p-1"><BsThreeDots/></summary>
                    <ul className="menu dropdown-content bg-secondary rounded-box z-1 w-52 p-2">
                        <li><a>
                            <IoPower className="text-warning text-lg"/> Set Offline
                        </a></li>
                        <li><a>
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
            <p className="text-accent">80%</p>
        </div>

        <progress className="progress progress-primary w-full mt-2" value={80} max="100"></progress>

        <div className="flex justify-between items-center text-sm my-2 text-secondary-content">
            <p>{lat}°, {lng}°</p>
            <p>Last ping 5 mins ago</p>
        </div>
    </div>);
}