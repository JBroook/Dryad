"use client"

import { Patrol, SerializedPatrolMember } from "@/app/home/patrols/page";
import ToggleGlowButton from "../ToggleGlowButton";
import { TbMapRoute, TbTrash } from "react-icons/tb";
import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/library/api";
import ProjectPatrolCard from "../ProjectPatrolCard";
import { RxCross2 } from "react-icons/rx";
import { FaPlus } from "react-icons/fa";
import CenteredCard from "../CenteredCard";
import { PiMagicWand } from "react-icons/pi";
import dynamic from "next/dynamic";
import type { GeoJSON } from 'geojson';
import type { FeatureGroup as LeafletFeatureGroup } from "leaflet";
import Waypoint from "../Waypoint";

const PatrolCreationMap = dynamic(() => import("../PatrolCreationMap"), {
    ssr: false,
});


interface DevicesViewProps {
    projectID : string | null;
    geoJSON : GeoJSON | null | undefined;
    gridCells : any;
}

export default function DevicesView(props: DevicesViewProps) {
    const [patrols, setPatrols] = useState<Patrol[]>([]);
    const [filterIndex, setFilterIndex] = useState<number>(1);
    const [isCreatingPatrol, setIsCreatingPatrol] = useState<boolean>(false);
    const filterOptions = [
        {title : "All", key : "all", count : patrols.length},
        {title : "Pending", key : "pending", count : patrols.reduce((count, patrol)=> {return patrol.status === "pending" ? (count + 1) : count}, 0)},
        {title : "Completed", key : "completed", count : patrols.reduce((count, patrol)=> {return patrol.status === "completed" ? (count + 1) : count}, 0)},
        {title : "Cancelled", key : "cancelled", count : patrols.reduce((count, patrol)=> {return patrol.status === "cancelled" ? (count + 1) : count}, 0)},
    ]
    const drawnItemsReference = useRef<LeafletFeatureGroup | null>(null);
  
    const extractPatrols = (data : any)=>{
        setPatrols(data.map((patrol : any)=>{
        const incident = patrol.incident;
        return {...patrol,
            assignedBy : {
            ...patrol.assigned_by,
            firstName : patrol.assigned_by.user.first_name,
            lastName : patrol.assigned_by.user.last_name,
            },
            assignedMembers : patrol.members.map((member : SerializedPatrolMember) => ({
            id : member.id,
            firstName : member.user.first_name,
            lastName : member.user.last_name,
            role : member.role,
            })),
            assignedAt : patrol.assigned_at,
            incident : {
            ...incident,
            threatClass : incident.threat_class,
            coordinates : {
                lat : parseFloat(incident.coordinates.coordinates[0]),
                lng : parseFloat(incident.coordinates.coordinates[1])
            }
            }
        }
        }))
    }

    useEffect(()=>{
        // fetch project patrols
        apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/patrols/`)
        .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
        })
        .then((data)=>{console.log(data); return data})
        .then((data)=>extractPatrols(data))
        .catch((err) => console.error("Fetch failed:", err));

        import("cally");
    },[])
    
    let matchingPatrols = patrols;

    if(filterIndex!=0){
    matchingPatrols = patrols.filter(patrol => patrol.status===filterOptions[filterIndex].key)
    }
    
    return (<>
    {!isCreatingPatrol ?
        <>
        <div className="flex gap-2 mx-6 mt-4 items-center">
            {filterOptions.map((option, index)=>{
                return <ToggleGlowButton
                key={index}
                color="#34D399"
                active={filterIndex===index}
                onClick={()=>setFilterIndex(index)}
                >
                {option.title} ({option.count})
                </ToggleGlowButton>
            })}

            <p className="text-secondary-content ml-auto">
                {patrols.length} patrols
            </p>
            <button className="btn btn-primary ml-2" onClick={()=>setIsCreatingPatrol(true)}>
                <FaPlus/> New Patrol    
            </button>
        </div>

        <div className="mx-6 mt-5">
        {matchingPatrols.length>0 ?
            matchingPatrols.map((patrol, index)=>{
            return <ProjectPatrolCard
                key={index}
                color="#F97316"
                patrol={patrol}
                cancelPatrol={()=>{}}
            />
        })
        :
        <div className="w-full flex flex-col justify-center items-center text-secondary-content pt-30">
            <TbMapRoute className="text-4xl"/>
            
            {filterOptions[filterIndex].key!=="all" ? 
            <h1>This project has no {filterOptions[filterIndex].key} patrols</h1>
            :
            <h1>This project has no patrols</h1>
            }
            <p className="text-sm">Assign a patrol or create one to get started</p>
        </div>
        }
        </div>
        </>
        :
        <>
        <div className="flex items-center mx-6 mt-3 ">
            <div className="rounded-xl bg-base-300 p-3 border border-white/15 mt-2">
                <TbMapRoute className="text-xl text-primary"/>
            </div>

            <div className="ml-4 flex-1 mt-2">
                <h1 className="font-semibold text-lg">Create a Routine Patrol</h1>
                <p className="text-secondary-content text-sm">Set a patrol path that repeats on a timely basis</p>
            </div>

            <button onClick={()=>setIsCreatingPatrol(false)}
                className="btn btn-secondary font-medium">
                <RxCross2 className="text-xl"/>
                Cancel
            </button>
        </div>

        <div className="flex mx-6 mt-6">
            <div className="flex-2 mb-20">
                <div className="rounded-xl bg-base-200 p-6 border border-white/8">
                    <h1 className="font-semibold">Patrol Details</h1>
                    <form>
                        <fieldset className="fieldset flex-1">
                        <legend className="fieldset-legend font-medium text-secondary-content">PATROL NAME</legend>
                        <input
                            type="text"
                            className="input w-full bg-base-200 border border-white/15 text-base-content"   
                            // value={firstNameInput}
                            // onChange={(e)=>setFirstNameInput(e.target.value)}
                        />
                        </fieldset>

                        <fieldset className="fieldset flex-1">
                        <legend className="fieldset-legend font-medium text-secondary-content">FREQUENCY</legend>
                        <select
                        className="select w-full bg-base-200 border"
                        >
                            <option value="once">Once</option>
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                        </select>
                        </fieldset>

                        <fieldset className="fieldset flex-1">
                        <legend className="fieldset-legend font-medium text-secondary-content">START DATE</legend>
                        </fieldset>
                    </form>

                    <button
                    popoverTarget="cally-popover1" style={{ anchorName: "--cally1" } as React.CSSProperties}
                    className="input w-full bg-base-200 border border-white/15 text-base-content" id="cally1"
                    >
                    Pick a date
                    </button>

                    <div
                    popover="auto" id="cally-popover1" className="dropdown bg-base-100 rounded-box shadow-lg"
                    style={{ positionAnchor: "--cally1" } as React.CSSProperties}
                    >
                    <calendar-date
                        className="cally"
                        onChange={(e) => {
                        }}
                    >
                        <svg aria-label="Previous" className="fill-current size-4"
                        slot="previous" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                        >
                        <path d="M15.75 19.5 8.25 12l7.5-7.5" />
                        </svg>

                        <svg aria-label="Next" className="fill-current size-4"
                        slot="next" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                        >
                        <path d="m8.25 4.5 7.5 7.5 7.5-7.5" />
                        </svg>

                        <calendar-month />
                    </calendar-date>
                    </div>
                </div>

                <div className="rounded-xl bg-base-200 p-6 border mt-4 border-white/8">
                    <h1 className="font-semibold">Route Summary</h1>
                    <div className="grid grid-cols-2 gap-2 mt-4">
                        <CenteredCard>
                            <h1 className="font-semibold">
                                0
                            </h1>
                            <p className="text-secondary-content text-xs">
                                Waypoints
                            </p>
                        </CenteredCard>
                        <CenteredCard>
                            <h1 className="font-semibold">
                                -
                            </h1>
                            <p className="text-secondary-content text-xs">
                                Est. Distance
                            </p>
                        </CenteredCard>
                        <CenteredCard>
                            <h1 className="font-semibold">
                                -
                            </h1>
                            <p className="text-secondary-content text-xs">
                                Est. Duration
                            </p>
                        </CenteredCard>
                        <CenteredCard>
                            <h1 className="font-semibold">
                                Weekly
                            </h1>
                            <p className="text-secondary-content text-xs">
                                Frequency
                            </p>
                        </CenteredCard>
                    </div>
                    <p className="mt-2 text-secondary-content text-sm text-center">At least two waypoints required</p>
                </div>

                <button className="btn btn-primary w-full mt-4">
                    Create Patrol
                </button>
            </div>


            <div className="flex-5">
                <div className="flex ml-6 items-center">
                    <button className="btn btn-accent">
                        <PiMagicWand className="text-xl"/>
                        Auto-Generate Path
                    </button>

                    <p className="text-secondary-content text-sm ml-auto">
                        Click on the map to add waypoints
                    </p>
                </div>

                <div className="ml-6 mt-2 min-h-120">
                    <PatrolCreationMap
                    drawingEnabled={true}
                    drawnItemsReference={drawnItemsReference}
                    geoJSON={props.geoJSON ?? null}
                    gridCells={props.gridCells}
                    gridOpacity={0.7}
                    incidents={[]}
                    devices={[]}
                    handlePath={()=>{}}
                    />
                </div>

                <div className="rounded-xl bg-base-200 p-6 border border-white/8 ml-6 mt-4">
                    <h1 className="font-semibold">
                        Waypoints
                    </h1>

                    <Waypoint
                        count={1}
                        coords="1.194°, 113.816°"
                        deleteEvent={()=>{}}
                    />
                </div>
            </div>
        </div>
        </>
    }
    </>);
}