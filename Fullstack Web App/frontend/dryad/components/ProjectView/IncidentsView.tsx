import { HiOutlineFilter } from "react-icons/hi";
import Incident from "../Incident";
import { FaTruck } from "react-icons/fa";
import type { IncidentType } from "@/app/home/project/page";
import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { FaPersonCircleCheck } from "react-icons/fa6";
import { IoSearch } from "react-icons/io5";
import { Member } from "@/app/home/projects/new/page";
import MemberOption from "../MemberOption";

interface IncidentsViewProps {
    projectID : string | null;
    filterOptions : string[];
    filterIndex : number;
    setFilterIndex : (index : number) => void;
    incidents : IncidentType[];
    members : Member[];
}

export default function IncidentsView(props: IncidentsViewProps) {
    const [incidentIndex, setIncidentIndex] = useState<number>(-1);

    const confirmModal = (index : number)=>{
        const modal = document.getElementById('confirmModal') as HTMLDialogElement;
        modal.showModal();
        setIncidentIndex(index);
    }

    const dismissModal = (index : number)=>{
        const modal = document.getElementById('dismissModal') as HTMLDialogElement;
        modal.showModal();
        setIncidentIndex(index);
    }

    const assignPatrolModal = (index : number)=>{
        const modal = document.getElementById('assignPatrolModal') as HTMLDialogElement;
        modal.showModal();
        setIncidentIndex(index);
    }

    const confirmIncident = async (e : React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();

        await apiFetch(`http://127.0.0.1:8000/api/incidents/${props.incidents[incidentIndex].id}/`, {
            method : "PATCH",
            headers : {
                "Content-Type" : "application/json"
            },
            body : JSON.stringify({
                status : "confirmed"
            })
        })
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .catch((err) => console.error("Fetch failed:", err));

        const modal = document.getElementById('confirmModal') as HTMLDialogElement;
        modal.close();
    }

    const dismissIncident = async (e : React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();

        await apiFetch(`http://127.0.0.1:8000/api/incidents/${props.incidents[incidentIndex].id}/`, {
            method : "PATCH",
            headers : {
                "Content-Type" : "application/json"
            },
            body : JSON.stringify({
                status : "dismissed"
            })
        })
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .catch((err) => console.error("Fetch failed:", err));

        const modal = document.getElementById('dismissModal') as HTMLDialogElement;
        modal.close();
    }

    const assignPatrol = async (e : React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();

        // await apiFetch(`http://127.0.0.1:8000/api/members/?project=${props.projectID}/`, {
        //     method : "PATCH",
        //     headers : {
        //         "Content-Type" : "application/json"
        //     },
        //     body : JSON.stringify({
        //         status : "dismissed"
        //     })
        // })
        // .then(async (res) => {
        //     if (!res.ok) throw new Error(await res.text());
        //     return res.json();
        // })
        // .catch((err) => console.error("Fetch failed:", err));

        const modal = document.getElementById('assignPatrolModal') as HTMLDialogElement;
        modal.close();
    }

    return (<>
    <dialog id="confirmModal" className="modal">
        <div className="modal-box bg-base-200 border border-white/8">
            <h3 className="font-bold text-lg">Confirm Incident?</h3>
            <p className="py-4 text-sm text-secondary-content">
                This action will log the incident as valid, which allows Dryad to learn the behaviour of loggers.
                Only press "Confirm" if you have validated the logging incident.
            </p>
            <p className="text-warning text-sm"><i>
                False confirmations may affect Dryad's predictions    
            </i></p>
            <div className="modal-action">
            <form onSubmit={confirmIncident}>
                {/* if there is a button in form, it will close the modal */}
                <button type="submit" className="btn btn-primary mr-2">Confirm</button>
                <button formMethod="dialog" className="btn btn-secondary">Cancel</button>
            </form>
            </div>
        </div>
    </dialog>

    <dialog id="dismissModal" className="modal">
        <div className="modal-box bg-base-200 border border-white/8">
            <h3 className="font-bold text-lg">Dismiss Incident?</h3>
            <p className="py-4 text-sm text-secondary-content">
                This action will log the incident as invalid, ensuring Dryad does not take this incident into account for future predictions.
                Only press "Dismiss" if you are sure.
            </p>
            <p className="text-warning text-sm"><i>
                False dismissals may reduce Dryad's predictive capabilities.
            </i></p>
            <div className="modal-action">
            <form onSubmit={dismissIncident}>
                {/* if there is a button in form, it will close the modal */}
                <button type="submit" className="btn btn-error mr-2">Dismiss</button>
                <button formMethod="dialog" className="btn btn-secondary">Cancel</button>
            </form>
            </div>
        </div>
    </dialog>

    <dialog id="assignPatrolModal" className="modal">
        <div className="modal-box bg-base-200 border border-white/8">
            <h3 className="font-bold text-lg flex items-center">
                <FaPersonCircleCheck className="text-accent mr-2 text-xl"/>    
                Assign Patrol
            </h3>
            <p className="py-2 text-sm text-secondary-content">
                Dispatch a project member to investigate
            </p>
            <label className="input bg-secondary w-full border border-white/8 mt-2">
                <IoSearch />
                <input type="search" className="grow" placeholder="Search by name or email..." />
            </label>
            <div className="divider"></div>
            <div className="max-h-64 overflow-y-auto px-1">
                {props.members.map((member, index)=>{
                    return (<MemberOption member={member} key={index}/>)
                })}
            </div>

            <div className="modal-action">
            <form onSubmit={assignPatrol} className="w-full flex">
                {/* if there is a button in form, it will close the modal */}
                <button type="submit" className="btn btn-primary mr-4 flex-1">
                    <FaPersonCircleCheck className="text-xl"/>
                    Assign
                </button>
                <button formMethod="dialog" className="btn btn-secondary flex-1 border border-white/8">Cancel</button>
            </form>
            </div>
        </div>
    </dialog>

    <div className="ml-6 flex flex-row items-center mt-5">
        <HiOutlineFilter className="text-secondary-content text-lg"/>
        {props.filterOptions.map((filterOption, index)=>{
        return (
        <button 
            className={index!=props.filterIndex ? "btn btn-base-200 text-secondary-content border border-white/5 ml-2" :
            "btn bg-[#0A2513] text-accent border border-accent/50 ml-2"
            }
            key={index}
            onClick={()=>props.setFilterIndex(index)}>
            {filterOption}
        </button>)
        })}
    </div>

    <div className="mx-6 mt-5">
        {
            props.incidents.map((incident, index)=>{
                return <Incident
                    key={index}
                    color="#F97316"
                    icon={FaTruck}
                    name={incident.threatClass.name}
                    location={incident.coordinates}
                    timestamp={incident.timestamp}
                    device={incident.device.name}
                    confidence={incident.confidence}
                    confirmIncident={()=>confirmModal(index)}
                    dismissIncident={()=>dismissModal(index)}
                    assignPatrol={()=>assignPatrolModal(index)}
                    status={incident.status}
                />
            })
        }
    </div>
    </>);
}