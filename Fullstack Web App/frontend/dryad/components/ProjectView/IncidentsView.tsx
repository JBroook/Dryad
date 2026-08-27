"use client"

import { HiOutlineFilter } from "react-icons/hi";
import Incident from "../Incident";
import { FaTruck } from "react-icons/fa";
import type { IncidentType } from "@/app/home/project/page";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { FaMicrophone, FaPersonCircleCheck } from "react-icons/fa6";
import { IoSearch } from "react-icons/io5";
import { Member, ThreatClass } from "@/app/home/projects/new/page";
import MemberOption from "../MemberOption";
import GlowButton from "../GlowButton";
import { IoIosOptions, IoMdCheckmark } from "react-icons/io";
import { TbArrowsSort } from "react-icons/tb";
import SortButton from "../SortButton";
import ToggleGlowButton from "../ToggleGlowButton";
import getThreatIcon from "@/lib/threatIcons";
import { RxCross2 } from "react-icons/rx";

interface IncidentsViewProps {
    projectID : string | null;
    filterOptions : string[];
    filterIndex : number;
    setFilterIndex : (index : number) => void;
    incidents : IncidentType[];
    members : Member[];
    searchMember : (nameEmail : string) => void;
}


export default function IncidentsView(props: IncidentsViewProps) {
    const [incidentIndex, setIncidentIndex] = useState<number>(-1);
    const [selectedMembers, setSelectedMembers] = useState<Member[]>([]);
    const [search, setSearch] = useState<string>("");
    const [sortBy, setSortBy] = useState<string>("date");
    const [sortToggle, setSortToggle] = useState<{date : boolean, confidence : boolean}>({date : true, confidence : true});
    const [showFilters, setShowFilters] = useState<boolean>(false);
    const [threatClasses, setThreatClasses] = useState<ThreatClass[]>([
        {id : 0,
        name : "Chainsaw",
        description : "sound",
        active : false}
    ]);
    const [minimumConfidence, setMinimumConfidence] = useState<number>(25);
    type StatusKey = "reviewing" | "confirmed" | "dismissed";
    const [statusFilter, setStatusFilter] = useState<Record<StatusKey, boolean>>({
        reviewing : false,
        confirmed : false,
        dismissed : false
    });

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

        await apiFetch(`http://127.0.0.1:8000/api/patrols/`, {
            method : "POST",
            headers : {
                "Content-Type" : "application/json"
            },
            body : JSON.stringify(selectedMembers.map((member)=>{
                return {
                    member : member.id,
                    project : props.projectID,
                    target : props.incidents[incidentIndex].coordinates
                }
            }))
        })
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .catch((err) => console.error("Fetch failed:", err));

        const modal = document.getElementById('assignPatrolModal') as HTMLDialogElement;
        modal.close();
        setSelectedMembers([]);
    }

    const addMember = (index : number) => {
        if(selectedMembers.includes(props.members[index])){
            setSelectedMembers(newSelection => newSelection.filter(member => member!=props.members[index]))
        }else{
            setSelectedMembers([
                ...selectedMembers,
                props.members[index]
            ])
        }
    }

    const closeModal = (id : string) => {
        const modal = document.getElementById(id) as HTMLDialogElement;
        modal.close();
    }

    const handleSort = (type: "date" | "confidence") => {
        if (sortBy !== type) {
            setSortBy(type)
        } else {
            setSortToggle(prev => ({
                ...prev,
                [type]: !prev[type]
            }))
        }
    }

    const toggleThreatClass = (index : number) => {
        const newThreatClasses = [...threatClasses]
        newThreatClasses[index].active = !newThreatClasses[index].active;
        setThreatClasses(newThreatClasses);
    }

    const minimumConfidenceOptions = [
        {name : "All", value : 0},
        {name : "60%", value : 60},
        {name : "75%", value : 75},
        {name : "85%", value : 85},
        {name : "90%", value : 95},
    ]

    const statusOptions = [
        {name : "Reviewing", color : "#F59E0B", value : "reviewing" as StatusKey},
        {name : "Confirmed", color : "#4ADE80", value : "confirmed" as StatusKey},
        {name : "Dismissed", color : "#94A3B8", value : "dismissed" as StatusKey},
    ]

    useEffect(() => {
        const timeout = setTimeout(() => {
            props.searchMember(search)
        }, 500);

        return () => clearTimeout(timeout);
    }, [search]);


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
                <button type="submit" className="btn btn-primary mr-2">Confirm</button>
                <button 
                type="button"
                onClick={() => closeModal("confirmModal")} className="btn btn-secondary">Cancel</button>
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
                <button type="submit" className="btn btn-error mr-2">Dismiss</button>
                <button 
                type="button"
                onClick={() => closeModal("dismissModal")} className="btn btn-secondary">Cancel</button>
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
                <input type="search" className="grow" placeholder="Search by name or email..." onChange={(e)=>setSearch(e.target.value)} />
            </label>
            <div className="divider"></div>
            <div className="max-h-64 overflow-y-auto px-1">
                {props.members.map((member, index)=>{
                    return (<MemberOption 
                        member={member} 
                        key={index} 
                        addMember={()=>addMember(index)}
                        selected={selectedMembers.includes(member)}/>
                    )
                })}
            </div>
            
            {selectedMembers.length>0 &&
                <p className="mt-2 font-semibold">
                    Assign to: {selectedMembers.map((member : Member)=>{
                        return member.firstName + " " + member.lastName
                    }).join(", ")}
                </p>
            }
            <div className="modal-action">
            <form onSubmit={assignPatrol} className="w-full flex">
                <button 
                type="submit" 
                className="btn btn-primary mr-4 flex-1"
                disabled={selectedMembers.length==0}>
                    <FaPersonCircleCheck className="text-xl"/>
                    Assign
                </button>
                <button 
                className="btn btn-secondary flex-1 border border-white/8"
                type="button"
                onClick={() => closeModal("assignPatrolModal")}
                >Cancel</button>
            </form>
            </div>
        </div>
    </dialog>

    <div className="mx-6 flex flex-row items-center mt-5">
        <label className="input bg-secondary w-full border border-white/8 flex-1">
            <IoSearch />
            <input 
            type="search" 
            className="grow" 
            placeholder="Search" 
            onChange={(e)=>setSearch(e.target.value)} />
        </label>

        <GlowButton color="#4ADE80" className="mx-2" onClick={()=>setShowFilters(!showFilters)}>
            <IoIosOptions />
            Filters
        </GlowButton>

        <p className="mx-2 text-sm text-secondary-content">Sort:</p>

        
        <SortButton 
        active={sortBy=="date"} 
        className="mx-2" 
        onClick={()=>handleSort("date")}
        ascending={sortToggle["date"]}>
            Date
        </SortButton>

        <SortButton 
        active={sortBy=="confidence"} 
        className="mx-2" 
        onClick={()=>handleSort("confidence")}
        ascending={sortToggle["confidence"]}>
            Confidence
        </SortButton>
    </div>

    {showFilters && <div className="rounded-xl bg-base-200 border border-white/8 mx-6 my-4 p-4">
        <p className="font-semibold text-secondary-content text-sm">THREAT TYPE</p>
        <div className="flex flex-row gap-2 mt-2">
            {threatClasses.map((threatClass, index)=>{
                const Icon = getThreatIcon(threatClass.name);
                return( 
                <ToggleGlowButton 
                key={index} 
                color="#4ADE80" 
                active={threatClass.active}
                onClick={()=>toggleThreatClass(index)}>
                    <Icon />
                    {threatClass.name}
                </ToggleGlowButton>)}
            )}
        </div>

        <div className="divider"></div>

        <p className="font-semibold text-secondary-content text-sm">STATUS</p>
        <div className="flex flex-row gap-2 mt-2">
            {statusOptions.map((option, index)=>{
                return( 
                <ToggleGlowButton 
                key={index} 
                color={option.color} 
                active={statusFilter[option.value]}
                onClick={()=>setStatusFilter({
                    ...statusFilter,
                    [option.value] : !statusFilter[option.value]
                })}>
                    <IoMdCheckmark />
                    {option.name}
                </ToggleGlowButton>)}
            )}
        </div>

        <div className="divider"></div>

        <div className="flex justify-between">
            <p className="font-semibold text-secondary-content text-sm">MIN. CONFIDENCE</p>

            <h3 className="text-base text-accent font-semibold">
                ≥ {minimumConfidence}%
            </h3>
        </div>
        <div className="flex mt-2 items-center">
            <input 
                type="range"
                min={0} max="100" 
                value={minimumConfidence} 
                className="range range-primary w-full flex-1 mr-2"
                onChange={(e)=>setMinimumConfidence(parseInt(e.target.value))}
            />

            {
                minimumConfidenceOptions.map((option, index)=>{
                    return (
                    <ToggleGlowButton 
                        key={index}
                        className="ml-1"
                        active={minimumConfidence===option.value} 
                        color="#4ADE80"
                        onClick={()=>setMinimumConfidence(option.value)} > 
                        {option.name}
                    </ToggleGlowButton>)
                })
            }
        </div>

        <div className="divider"></div>

        <div className="flex">
            <GlowButton color="#F87171" className="ml-auto">
                <RxCross2 className="text-xl"/>
                Reset All Filters
            </GlowButton>
        </div>

    </div>}

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