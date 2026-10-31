"use client"

import Incident from "../Incident";
import { FaTruck } from "react-icons/fa";
import type { IncidentType } from "@/app/home/project/page";
import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/library/api";
import { FaPersonCircleCheck, FaPlus } from "react-icons/fa6";
import { IoSearch } from "react-icons/io5";
import { Member, ThreatClass } from "@/app/home/projects/new/page";
import MemberOption from "../MemberOption";
import GlowButton from "../GlowButton";
import { IoIosOptions, IoIosWarning, IoMdCheckmark } from "react-icons/io";
import SortButton from "../SortButton";
import ToggleGlowButton from "../ToggleGlowButton";
import getThreatIcon from "@/library/threatIcons";
import { RxCross2 } from "react-icons/rx";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "../ToastProvider";

interface IncidentsViewProps {
    projectID : string | null;
    filterOptions : string[];
    filterIndex : number;
    setFilterIndex : (index : number) => void;
    incidents : IncidentType[];
    threatClasses : ThreatClass[];
    projectThreatClassIds: number[];
    setThreatClasses : (newThreatClasses : ThreatClass[]) => void;
    setIncidents : (incidents : IncidentType[]) => void;
    canManage: boolean;
}

const getLocalDateTimeValue = () => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
};


export default function IncidentsView(props: IncidentsViewProps) {
    const { showToast } = useToast();
    const [incidentIndex, setIncidentIndex] = useState<number>(-1);
    const [members, setMembers] = useState<Member[]>([]);
    const [selectedMembers, setSelectedMembers] = useState<Member[]>([]);
    const [searchMember, setSearchMember] = useState<string>("");
    const [searchIncident, setSearchIncident] = useState<string>("");
    const [sortBy, setSortBy] = useState<string>("date");
    const [sortToggle, setSortToggle] = useState<{date : boolean, confidence : boolean}>({date : true, confidence : true});
    const [showFilters, setShowFilters] = useState<boolean>(false);
    const [minimumConfidence, setMinimumConfidence] = useState<number>(0);
    const [manualThreatClass, setManualThreatClass] = useState("");
    const [manualTimestamp, setManualTimestamp] = useState(getLocalDateTimeValue);
    const [manualLatitude, setManualLatitude] = useState("");
    const [manualLongitude, setManualLongitude] = useState("");
    const [isCreatingManualReport, setIsCreatingManualReport] = useState(false);
    const [isGettingLocation, setIsGettingLocation] = useState(false);
    type StatusKey = "new" | "reviewing" | "confirmed" | "dismissed";
    const [statusFilter, setStatusFilter] = useState<Record<StatusKey, boolean>>({
        new : false,
        reviewing : false,
        confirmed : false,
        dismissed : false
    });

    const searchParams = useSearchParams();
    const projectID = searchParams.get("pid");

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

        await apiFetch(`incidents/${props.incidents[incidentIndex].id}/`, {
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
        .then((data)=>{
            const newIncidents = [...props.incidents]
            newIncidents[incidentIndex].status = "confirmed"
            props.setIncidents(newIncidents)
            showToast(data.message ?? "Incident confirmed successfully.");
        })
        .catch((err) => {
            console.error("Incident confirmation failed:", err);
            showToast("Unable to confirm this incident.", "error");
        });

        const modal = document.getElementById('confirmModal') as HTMLDialogElement;
        modal.close();
    }

    const dismissIncident = async (e : React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();

        await apiFetch(`incidents/${props.incidents[incidentIndex].id}/`, {
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
        .then((data)=>{
            const newIncidents = [...props.incidents]
            newIncidents[incidentIndex].status = "dismissed"
            props.setIncidents(newIncidents)
            showToast(data.message ?? "Incident dismissed successfully.");
        })
        .catch((err) => {
            console.error("Incident dismissal failed:", err);
            showToast("Unable to dismiss this incident.", "error");
        });

        const modal = document.getElementById('dismissModal') as HTMLDialogElement;
        modal.close();
    }

    const assignPatrol = async (e : React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();

        const currentUserId = Number(localStorage.getItem("userID"));
        const currentUserMembershipId = members.find((member) => member.user?.id === currentUserId)?.id;

        if (!currentUserMembershipId) {
            console.error("Current user membership ID could not be found for this project.");
            return;
        }

        try {
            const res = await apiFetch(`incidents/${props.incidents[incidentIndex].id}/assign_patrol`, {
                method : "POST",
                body : JSON.stringify({
                    assignee_ids : selectedMembers.map((member) => member.id),
                    assigner_id : currentUserMembershipId
                })
            });

            if (!res.ok) {
                throw new Error(await res.text());
            }
            const data = await res.json();
            showToast(data.message ?? "Patrol assigned successfully.");
        } catch (err) {
            console.error("Fetch failed:", err);
            showToast("Unable to assign a patrol to this incident.", "error");
            return;
        }

        const modal = document.getElementById('assignPatrolModal') as HTMLDialogElement;
        modal.close();
        setSelectedMembers([]);
    }

    const addMember = (index : number) => {
        if(selectedMembers.includes(members[index])){
            setSelectedMembers(newSelection => newSelection.filter(member => member!=members[index]))
        }else{
            setSelectedMembers([
                ...selectedMembers,
                members[index]
            ])
        }
    }

    const closeModal = (id : string) => {
        const modal = document.getElementById(id) as HTMLDialogElement;
        modal.close();
    }

    const manualThreatClasses = props.threatClasses.filter((threatClass) =>
        props.projectThreatClassIds.includes(threatClass.id)
    );

    const openManualReportModal = () => {
        setManualThreatClass(manualThreatClasses[0]?.id.toString() ?? "");
        setManualTimestamp(getLocalDateTimeValue());
        setManualLatitude("");
        setManualLongitude("");
        const modal = document.getElementById("manualReportModal") as HTMLDialogElement;
        modal.showModal();
    };

    const fillCurrentLocation = () => {
        if (!navigator.geolocation) {
            showToast("Location is not available in this browser.", "error");
            return;
        }

        setIsGettingLocation(true);
        navigator.geolocation.getCurrentPosition(
            ({ coords }) => {
                setManualLatitude(coords.latitude.toString());
                setManualLongitude(coords.longitude.toString());
                setIsGettingLocation(false);
            },
            (error) => {
                console.error("Could not retrieve current location:", error);
                showToast("Unable to retrieve your current location.", "error");
                setIsGettingLocation(false);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    };

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

    const filterSortIncidents = async ({
        minConfidence = minimumConfidence,
        status = statusFilter,
        threatClasses = props.threatClasses,
        sortKey = sortBy,
        sortToggles = sortToggle
    }: {
        minConfidence?: number;
        status?: Record<StatusKey, boolean>;
        threatClasses?: ThreatClass[];
        sortKey? : string;
        sortToggles? : {date : boolean, confidence : boolean}
    } = {}) => {
        const params = new URLSearchParams();
        params.set("minimum_confidence", minConfidence.toString());

        const statuses = Object.keys(status)
            .filter(key => status[key as StatusKey]===true)

        statuses.forEach(status => {
            params.append("status", status)
        })

        const threats = threatClasses
            .filter(threatClass => threatClass.active==true)
            .map((threatClass : ThreatClass)=> threatClass.id)    
        if (threats.length > 0) {
            params.set("threat_classes", threats.join(","));
        }

        const sortKeyMapping = {
            "date" : "timestamp",
            "confidence" : "confidence"
        }
        params.set("ordering", `${sortToggles[sortKey as "date" | "confidence"] ? "-" : ""}${sortKeyMapping[sortKey as "date" | "confidence"]}`)

        await apiFetch(
            `incidents?project=${props.projectID}&${params}`)
        .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
        })
        .then((data)=>extractIncidents(data))
        .catch((err) => console.error("Fetch failed:", err));
    }

    const toggleThreatClass = (index: number) => {
        const newThreatClasses = props.threatClasses.map((threatClass, i) =>
            i === index
                ? { ...threatClass, active: !threatClass.active }
                : threatClass
        );

        props.setThreatClasses(newThreatClasses);
        filterSortIncidents({ threatClasses: newThreatClasses });
    };

    const minimumConfidenceOptions = [
        {name : "All", value : 0},
        {name : "60%", value : 60},
        {name : "75%", value : 75},
        {name : "85%", value : 85},
        {name : "90%", value : 90},
    ]

    const statusOptions = [
        {name : "New", color : "#F59E0B", value : "new" as StatusKey},
        {name : "Reviewing", color : "#F59E0B", value : "reviewing" as StatusKey},
        {name : "Confirmed", color : "#4ADE80", value : "confirmed" as StatusKey},
        {name : "Dismissed", color : "#94A3B8", value : "dismissed" as StatusKey},
    ]

    const resetFilters = () => {
        const newThreatClasses = props.threatClasses.map(
            (threatClass: ThreatClass) => ({
                ...threatClass,
                active: false
            })
        );

        const newStatusFilter: Record<StatusKey, boolean> = {
            new : false,
            reviewing: false,
            confirmed: false,
            dismissed: false
        };

        setMinimumConfidence(0);
        props.setThreatClasses(newThreatClasses);
        setStatusFilter(newStatusFilter);

        filterSortIncidents({
            minConfidence: 0,
            status: newStatusFilter,
            threatClasses: newThreatClasses
        });
    };


    const apiSearchMember = async (nameEmail : string) => {
        await apiFetch(`projects/${props.projectID}/members?search=${nameEmail}`)
        .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
        })
        .then((data)=>setMembers(data.map((member : any)=>{
        return {...member, 
            firstName : member.user.first_name, 
            lastName : member.user.last_name,
            email : member.user.email,
            profilePicture: member.user.profile_picture,
            joinDate : member.join_date
        }
        })))
        .catch((err) => console.error("Fetch failed:", err));
    }

    const normalizeIncident = (incident: any): IncidentType => ({
        ...incident,
        threatClass: incident.threat_class,
        coordinates: {
            lat: parseFloat(incident.coordinates.coordinates[0]),
            lng: parseFloat(incident.coordinates.coordinates[1])
        }
    });

    const extractIncidents = (data : any)=>{
        props.setIncidents(data.map(normalizeIncident));
    }

    const createManualReport = async (e: React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsCreatingManualReport(true);

        try {
            const response = await apiFetch(`projects/${props.projectID}/manual_reports`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    threat_class: Number(manualThreatClass),
                    timestamp: new Date(manualTimestamp).toISOString(),
                    latitude: Number(manualLatitude),
                    longitude: Number(manualLongitude),
                }),
            });
            if (!response.ok) throw new Error(await response.text());

            const data = await response.json();
            props.setIncidents([
                {
                    ...normalizeIncident(data),
                    coordinates: {
                        lat: Number(manualLatitude),
                        lng: Number(manualLongitude),
                    },
                },
                ...props.incidents,
            ]);
            closeModal("manualReportModal");
            showToast("Manual incident report created successfully.");
        } catch (error) {
            console.error("Manual incident report creation failed:", error);
            showToast("Unable to create the manual incident report.", "error");
        } finally {
            setIsCreatingManualReport(false);
        }
    };

    const apiSearchIncident = async (incidentName : string) => {
        await apiFetch(`incidents?project=${props.projectID}&search=${incidentName}`)
        .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
        })
        .then((data)=>extractIncidents(data))
        .catch((err) => console.error("Fetch failed:", err));
    }

    useEffect(() => {
        const timeout = setTimeout(() => {
            apiSearchMember(searchMember)
        }, 250);

        return () => clearTimeout(timeout);
    }, [searchMember]);

    const router = useRouter();

    const isFirstRender = useRef(true);
    useEffect(() => {

        if (isFirstRender.current) {
            isFirstRender.current = false;
            return;
        }

        const timeout = setTimeout(() => {
            apiSearchIncident(searchIncident)
        }, 250);

        return () => clearTimeout(timeout);
    }, [searchIncident]);


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
                Dispatch selected project members to investigate together
            </p>
            <label className="input bg-secondary w-full border border-white/8 mt-2">
                <IoSearch />
                <input type="search" className="grow" placeholder="Search by name or email..." onChange={(e)=>setSearchMember(e.target.value)} />
            </label>
            <div className="divider"></div>
            <div className="max-h-64 overflow-y-auto px-1">
                {members.map((member, index)=>{
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

    <dialog id="manualReportModal" className="modal">
        <div className="modal-box bg-base-200 border border-white/8">
            <h3 className="font-bold text-lg">New Manual Incident Report</h3>
            <p className="py-2 text-sm text-secondary-content">
                Enter the incident details and location.
            </p>
            <form onSubmit={createManualReport} className="space-y-2">
                <div className="form-control w-full">
                    <span className="label-text mb-2 text-sm font-semibold">Threat</span>
                    <select
                        className="select select-bordered w-full border border-white/10 bg-secondary"
                        value={manualThreatClass}
                        onChange={(event) => setManualThreatClass(event.target.value)}
                        required
                    >
                        <option value="" disabled>Select a threat</option>
                        {manualThreatClasses.map((threatClass) => (
                            <option key={threatClass.id} value={threatClass.id}>
                                {threatClass.name}
                            </option>
                        ))}
                    </select>
                </div>

                {manualThreatClasses.length === 0 && (
                    <p className="text-sm text-warning">
                        No threat types are configured for this project.
                    </p>
                )}

                <div className="form-control w-full">
                    <span className="label-text mb-2 text-sm font-semibold">Date and time</span>
                    <input
                        type="datetime-local"
                        className="input input-bordered w-full border border-white/10 bg-secondary"
                        value={manualTimestamp}
                        onChange={(event) => setManualTimestamp(event.target.value)}
                        required
                    />
                </div>

                <div className="grid grid-cols-2 gap-3 mt-2">
                    <label className="form-control">
                        <span className="label-text mb-2 text-sm font-semibold">Latitude</span>
                        <input
                            type="number"
                            step="any"
                            className="input input-bordered w-full border border-white/10 bg-secondary"
                            value={manualLatitude}
                            onChange={(event) => setManualLatitude(event.target.value)}
                            required
                        />
                    </label>
                    <label className="form-control">
                        <span className="label-text mb-2 text-sm font-semibold">Longitude</span>
                        <input
                            type="number"
                            step="any"
                            className="input input-bordered w-full border border-white/10 bg-secondary"
                            value={manualLongitude}
                            onChange={(event) => setManualLongitude(event.target.value)}
                            required
                        />
                    </label>
                </div>

                <button
                    type="button"
                    className="btn btn-primary w-full"
                    onClick={fillCurrentLocation}
                    disabled={isGettingLocation}
                >
                    {isGettingLocation ? "Getting location..." : "Use Current Location"}
                </button>

                <div className="modal-action">
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={isCreatingManualReport || manualThreatClasses.length === 0}
                    >
                        {isCreatingManualReport ? "Creating..." : "Create report"}
                    </button>
                    <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => closeModal("manualReportModal")}
                    >
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    </dialog>

    <div className="mx-6 flex flex-row items-center mt-5">
        <label className="input bg-secondary w-full border border-white/8 flex-1">
            <IoSearch />
            <input 
            type="search" 
            className="grow" 
            placeholder="Search" 
            value={searchIncident}
            onChange={(e)=>setSearchIncident(e.target.value)} />
        </label>

        <ToggleGlowButton active={showFilters} color="#4ADE80" className="mx-2" onClick={()=>setShowFilters(!showFilters)}>
            <IoIosOptions />
            Filters
        </ToggleGlowButton>

        <p className="mx-2 text-sm text-secondary-content">Sort:</p>

        
        <SortButton 
        active={sortBy=="date"} 
        className="mx-2" 
        onClick={()=>{
            filterSortIncidents({
                sortKey : "date",
                sortToggles : {...sortToggle, date : !sortToggle.date}
            })
            handleSort("date")
        }}
        ascending={sortToggle["date"]}>
            Date
        </SortButton>

        <SortButton 
        active={sortBy=="confidence"} 
        className="mx-2" 
        onClick={()=>{
            filterSortIncidents({
                sortKey : "confidence",
                sortToggles : {...sortToggle, confidence : !sortToggle.confidence}
            })
            handleSort("confidence")
        }}
        ascending={sortToggle["confidence"]}>
            Confidence
        </SortButton>

        {props.canManage && <button className="btn btn-primary ml-2" onClick={openManualReportModal}>
            <FaPlus/> New Incident
        </button>}
    </div>
    

    {showFilters && <div className="rounded-xl bg-base-200 border border-white/8 mx-6 my-4 p-4">
        <p className="font-semibold text-secondary-content text-sm">THREAT TYPE</p>
        <div className="flex flex-row gap-2 mt-2">
            {props.threatClasses.map((threatClass, index)=>{
                const Icon = getThreatIcon(threatClass.name);
                return( 
                <ToggleGlowButton 
                key={index} 
                color="#4ADE80" 
                active={threatClass.active}
                onClick={()=>{
                    toggleThreatClass(index)
                }}>
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
                onClick={()=>{
                    const newStatusFilter = {
                        ...statusFilter,
                        [option.value]: !statusFilter[option.value]
                    };

                    setStatusFilter(newStatusFilter);
                    filterSortIncidents({ status: newStatusFilter });
                }}>
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
                min={0}
                max={100}
                value={minimumConfidence}
                className="range range-primary w-full flex-1 mr-2"
                onChange={(e) => {
                    const value = parseInt(e.target.value);

                    setMinimumConfidence(value);
                    filterSortIncidents({ minConfidence: value });
                }}
            />

            {
                minimumConfidenceOptions.map((option, index)=>{
                    return (
                    <ToggleGlowButton 
                        key={index}
                        className="ml-1"
                        active={minimumConfidence===option.value} 
                        color="#4ADE80"
                        onClick={() => {
                            setMinimumConfidence(option.value);
                            filterSortIncidents({ minConfidence: option.value });
                        }}
                        > 
                        {option.name}
                    </ToggleGlowButton>)
                })
            }
        </div>

        <div className="divider"></div>

        <div className="flex">
            <GlowButton color="#F87171" className="ml-auto" onClick={resetFilters}>
                <RxCross2 className="text-xl"/>
                Reset All Filters
            </GlowButton>
        </div>

    </div>}

    <div className="mx-6 mt-5">
        {props.incidents.length>0 ?
            props.incidents.map((incident, index)=>{
                return <Incident
                    key={incident.id}
                    name={incident.threatClass.name}
                    manualReport={incident.manual_report}
                    coordinates={incident.coordinates}
                    timestamp={incident.timestamp}
                    device={incident.device?.name ?? "Non-device"}
                    confidence={incident.confidence}
                    confirmIncident={()=>confirmModal(index)}
                    dismissIncident={()=>dismissModal(index)}
                    assignPatrol={()=>assignPatrolModal(index)}
                    status={incident.status}
                    projectID={parseInt(props.projectID!)}
                    canManage={props.canManage}
                />
            })
            :
            <div className="w-full flex flex-col justify-center items-center text-secondary-content pt-20">
                <IoIosWarning className="text-4xl"/>
                {searchIncident==="" ?
                <>
                    <h1>No incidents found</h1>
                    <p className="text-sm">Add a device to start recording incidents</p>
                    <button className="btn btn-primary mt-4" onClick={()=>router.push(`/home/project?pid=${props.projectID}&tab=devices`)}>
                        <FaPlus />
                        Add Device
                    </button>
                </> :
                    <h1>"{searchIncident}" couldn't be found</h1>
                }
            </div>
        }
    </div>
    </>);
}