import getThreatIcon from "@/library/threatIcons";
import { useState } from "react";
import { FaPersonRunning, FaRegClock } from "react-icons/fa6";
import { IoIosArrowDown, IoIosArrowUp } from "react-icons/io";
import { MdOutlineLocationOn } from "react-icons/md";
import GlowButton from "./GlowButton";
import { useRouter } from "next/navigation";
import { capitalizeFirstLetter } from "@/library/general";
import { ProjectOverview } from "@/app/home/project/page";

interface IncidentProps {
    name : string;
    coordinates : Coordinate;
    timestamp : string;
    device : string;
    confidence : number;
    confirmIncident? : ()=>void;
    dismissIncident? : ()=>void;
    assignPatrol? : ()=>void;
    status : string;
    projectID : number;
    mini? : boolean;
    canManage?: boolean;
    manualReport?: boolean;
}

export type Coordinate = {
    lat : number;
    lng : number;
}

export default function Incident(props : IncidentProps) {
    const Icon = getThreatIcon(props.name);
    const [isOpen, setIsOpen] = useState(false);
    const date = new Date(props.timestamp);

    const casualDate = date.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
    });

    const formalDateTime = date.toLocaleString("en-US");

    const router = useRouter();

    const getSeverityColor = (confidence: number) => {
        if (confidence >= 80) return "#d73027"; // very high
        if (confidence >= 60) return "#fc8d59"; // high
        if (confidence >= 40) return "#fee08b"; // medium
        if (confidence >= 20) return "#d9ef8b"; // low
        return "#91cf60";                  // very low
    };

    const color = getSeverityColor(props.confidence);
    const canManage = props.canManage ?? true;

    const getStatusBadege = (status : string) => {
        if (status==="new") return <div className="badge badge-soft badge-warning font-semibold">{capitalizeFirstLetter (props.status)}</div>;
        if (status==="reviewing") return <div className="badge badge-soft badge-warning font-semibold">{capitalizeFirstLetter (props.status)}</div>;
        if (status==="confirmed") return <div className="badge badge-soft badge-accent font-semibold">{capitalizeFirstLetter (props.status)}</div>;
        if (status==="dismissed") return <div className="badge badge-soft badge-error font-semibold">{capitalizeFirstLetter (props.status)}</div>;
    }

    const statusBadge = getStatusBadege(props.status);

    return (
    <div className="collapse mb-4 w-full rounded-2xl border border-2 border-white/5 bg-base-200 px-2">
        <input 
        type="checkbox" 
        className="p-0"
        checked={isOpen}
        onChange={(e) => setIsOpen(e.target.checked)}/>

        <div className="collapse-title flex flex-row items-center pr-2 md:pr-4">
            <div className="my-1 ml-1 h-full min-h-12 w-1 rounded-xs md:ml-2" style={{backgroundColor : color}} />

            {/* 1A appended to give 10% opacity */}
            <div className="ml-2 rounded-xl border p-2 md:ml-4 md:p-3" style={{backgroundColor : `${color}1A`, borderColor : `${color}1A`}}>
                <Icon className="text-xl" style={{color : color}}/>
            </div>

            <div className="ml-2 min-w-0 flex-1 md:ml-4">
                <div className="mb-1 flex flex-wrap items-center gap-1">
                    <h1 className="font-semibold">
                        {props.name}
                        {props.manualReport && <span className="ml-1 text-secondary-content">(Manual)</span>}
                    </h1>
                    {statusBadge}
                </div>

                <div className="flex flex-wrap items-center text-secondary-content text-xs md:flex-row md:text-sm">
                    <MdOutlineLocationOn className="mr-1"/> 
                    <p className="mr-3">{`${props.coordinates.lat?.toPrecision(5)}°, ${props.coordinates.lng?.toPrecision(5)}°`}</p>

                    <FaRegClock className="mr-1"/> 
                    <p className="mr-3">{casualDate}</p>

                    <p>Device: {props.device}</p>
                </div>
            </div>

            <div className="ml-auto flex shrink-0 flex-row items-center">
                {!props.manualReport && <div className="flex flex-col items-end">
                    <h1 className="font-semibold text-2xl text-accent">
                        {props.confidence}%
                    </h1>
                    <p className="text-secondary-content text-sm">confidence</p>
                </div>}

                {isOpen ?
                    <IoIosArrowUp className="text-2xl text-secondary-content ml-4" />
                    :
                    <IoIosArrowDown className="text-2xl text-secondary-content ml-4" />
                }
            </div>
        </div>

        <div className="collapse-content w-full">
            <div className="flex w-full flex-col gap-2 md:flex-row">
                <div className="flex-1 rounded-xl bg-secondary p-4 md:mr-2">
                    <p className="text-secondary-content text-sm mb-2">GPS Coordinates</p>
                    <h1>
                        {`${props.coordinates.lat?.toPrecision(5)}°, ${props.coordinates.lng?.toPrecision(5)}°`}
                    </h1>
                </div>

                <div className="flex-1 rounded-xl bg-secondary p-4 md:ml-2">
                    <p className="text-secondary-content text-sm mb-2">Exact Timestamp</p>
                    <h1>
                        {formalDateTime}
                    </h1>
                </div>
            </div>

            {!props.manualReport && <div className="w-full flex justify-between mt-4">
                <p className="text-secondary-content text-sm">
                    Confidence
                </p>
                <p className="text-accent text-sm text-end">
                    {props.confidence}%
                </p>
            </div>}

            {!props.manualReport && 
                <progress className="progress progress-primary w-full mt-2" value={props.confidence} max="100"></progress>
            }

            <div className="mt-2 flex flex-wrap gap-2">
                {(props.status=="new" && !props.mini && canManage) &&
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

                <button 
                className="btn btn-secondary hidden md:inline-flex"
                onClick={()=>router.push(`/home/project?pid=${props.projectID}&tab=forest_map&lat=${
                    props.coordinates.lng
                }&lng=${
                    props.coordinates.lat
                }`)}>
                    View on Map
                </button>

                {props.mini &&
                    <button 
                    className="btn btn-secondary hidden md:inline-flex"
                    onClick={()=>router.push(`/home/project?pid=${props.projectID}&tab=incidents`)}>
                        View Full
                    </button>}
            </div>
        </div>
    </div>);
}