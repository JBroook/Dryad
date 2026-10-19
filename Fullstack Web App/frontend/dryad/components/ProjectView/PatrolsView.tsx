"use client"

import { Patrol, SerializedPatrolMember } from "@/app/home/patrols/page";
import ToggleGlowButton from "../ToggleGlowButton";
import { TbMapRoute, TbTrash } from "react-icons/tb";
import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/library/api";
import ProjectPatrolCard from "../ProjectPatrolCard";
import RoutinePatrolCard from "../RoutinePatrolCard";
import { RxCross2 } from "react-icons/rx";
import { FaPlus } from "react-icons/fa";
import CenteredCard from "../CenteredCard";
import { PiMagicWand } from "react-icons/pi";
import dynamic from "next/dynamic";
import type { GeoJSON } from 'geojson';
import type { FeatureGroup as LeafletFeatureGroup } from "leaflet";
import Waypoint from "../Waypoint";
import { length as turfLength, lineString } from "@turf/turf";

export type RoutinePatrol = {
    id: number;
    name: string;
    frequency: string;
    start_date: string;
    path: {
        type: "LineString";
        coordinates: [number, number][];
    };
    created_at: string;
    created_by: {
        id: number;
        role: string;
        user: {
            first_name: string;
            last_name: string;
        };
    } | null;
    project: {
        id: number;
        name: string;
    };
};

const PatrolCreationMap = dynamic(() => import("../PatrolCreationMap"), {
    ssr: false,
});


interface DevicesViewProps {
    projectID : string | null;
    geoJSON : GeoJSON | null | undefined;
    gridCells : any;
    canManage: boolean;
}

export default function DevicesView(props: DevicesViewProps) {
    const [patrols, setPatrols] = useState<Patrol[]>([]);
    const [routinePatrols, setRoutinePatrols] = useState<RoutinePatrol[]>([]);
    const [routineFetchError, setRoutineFetchError] = useState("");
    const [filterIndex, setFilterIndex] = useState<number>(1);
    const [isCreatingPatrol, setIsCreatingPatrol] = useState<boolean>(false);
    const [patrolName, setPatrolName] = useState("Routine Patrol");
    const [frequency, setFrequency] = useState("weekly");
    const [startDate, setStartDate] = useState("");
    const [pathCoordinates, setPathCoordinates] = useState<[number, number][]>([]);
    const [isSavingPatrol, setIsSavingPatrol] = useState(false);
    const [isGeneratingPath, setIsGeneratingPath] = useState(false);
    const [creationError, setCreationError] = useState("");
    const [creationMessage, setCreationMessage] = useState("");
    const routeDistanceKm = pathCoordinates.length >= 2
        ? turfLength(
            lineString(pathCoordinates.map(([latitude, longitude]) => [longitude, latitude])),
            { units: "kilometers" }
        )
        : null;
    const routeDurationMinutes = routeDistanceKm === null
        ? null
        : Math.ceil(routeDistanceKm / 5 * 60);
    const formattedDistance = routeDistanceKm === null
        ? "-"
        : routeDistanceKm < 1
            ? `${Math.round(routeDistanceKm * 1000)} m`
            : `${routeDistanceKm.toFixed(2)} km`;
    const formattedDuration = routeDurationMinutes === null
        ? "-"
        : routeDurationMinutes < 60
            ? `${routeDurationMinutes} min`
            : `${Math.floor(routeDurationMinutes / 60)} h ${routeDurationMinutes % 60} min`;
    const filterOptions = [
        {title : "All", key : "all", count : patrols.length + routinePatrols.length},
        {title : "Pending", key : "pending", count : patrols.reduce((count, patrol)=> {return patrol.status === "pending" ? (count + 1) : count}, 0)},
        {title : "Completed", key : "completed", count : patrols.reduce((count, patrol)=> {return patrol.status === "completed" ? (count + 1) : count}, 0)},
        {title : "Cancelled", key : "cancelled", count : patrols.reduce((count, patrol)=> {return patrol.status === "cancelled" ? (count + 1) : count}, 0)},
        {title : "Routine", key : "routine", count : routinePatrols.length},
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
        if (!props.projectID) {
            return;
        }

        apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/patrols/`)
        .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
        })
        .then((data)=>extractPatrols(data))
        .catch((err) => console.error("Fetch failed:", err));

        apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/routine_patrols/`)
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .then((data: RoutinePatrol[]) => setRoutinePatrols(data))
        .catch((err) => {
            console.error("Routine patrol fetch failed:", err);
            setRoutineFetchError("Unable to load routine patrols.");
        });
    },[props.projectID])

    const createRoutinePatrol = async () => {
        setCreationError("");
        if (!props.projectID) {
            setCreationError("A project is required to create a routine patrol.");
            return;
        }
        if (patrolName.trim() === "" || startDate === "" || pathCoordinates.length < 2) {
            setCreationError("Enter a patrol name and start date, and draw a path with at least two waypoints.");
            return;
        }

        setIsSavingPatrol(true);
        try {
            const response = await apiFetch(
                `http://127.0.0.1:8000/api/projects/${props.projectID}/routine_patrols/`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        name: patrolName.trim(),
                        frequency,
                        start_date: startDate,
                        path: {
                            type: "LineString",
                            coordinates: pathCoordinates.map(([latitude, longitude]) => [
                                longitude,
                                latitude,
                            ]),
                        },
                    }),
                }
            );
            if (!response.ok) {
                throw new Error(await response.text());
            }

            const createdPatrol: RoutinePatrol = await response.json();
            setRoutinePatrols((current) => [createdPatrol, ...current]);
            setFilterIndex(filterOptions.findIndex((option) => option.key === "routine"));

            setCreationMessage("Routine patrol created.");
            setIsCreatingPatrol(false);

            setPatrolName("");
            setFrequency("weekly");
            setStartDate("");

            setPathCoordinates([]);
        } catch (error) {
            setCreationError(
                error instanceof Error ? error.message : "Unable to create the routine patrol."
            );
        } finally {
            setIsSavingPatrol(false);
        }
    };

    const autoGeneratePath = async () => {
        setCreationError("");
        if (!props.projectID) {
            setCreationError("A project is required to generate a patrol path.");
            return;
        }

        setIsGeneratingPath(true);
        try {
            const response = await apiFetch(
                `http://127.0.0.1:8000/api/projects/${props.projectID}/generate_routine_patrol_path/`,
                { method: "POST" }
            );
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail ?? "Unable to generate a patrol path.");
            }

            const data: {
                path: { type: "LineString"; coordinates: [number, number][] };
                hotspot_count: number;
            } = await response.json();
            setPathCoordinates(
                data.path.coordinates.map(([longitude, latitude]) => [latitude, longitude])
            );
        } catch (error) {
            setCreationError(
                error instanceof Error ? error.message : "Unable to generate a patrol path."
            );
        } finally {
            setIsGeneratingPath(false);
        }
    };
    
    const selectedFilter = filterOptions[filterIndex].key;
    const matchingPatrols = selectedFilter === "all"
        ? patrols
        : patrols.filter((patrol) => patrol.status === selectedFilter);
    const matchingRoutinePatrols = selectedFilter === "all" || selectedFilter === "routine"
        ? routinePatrols
        : [];
    const hasMatchingPatrols = matchingPatrols.length > 0 || matchingRoutinePatrols.length > 0;

    return (<>
    {!isCreatingPatrol ?
        <>
        {creationMessage && (
            <div role="status" className="alert alert-success mx-6 mt-3 hover:cursor-pointer" onClick={()=>setCreationMessage("")}>
                {creationMessage}
            </div>
        )}
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
                {patrols.length + routinePatrols.length} patrols
            </p>
            {props.canManage && <button className="btn btn-primary ml-2" onClick={()=>setIsCreatingPatrol(true)}>
                <FaPlus/> New Patrol    
            </button>}
        </div>

        <div className="mx-6 mt-5">
        {routineFetchError && (selectedFilter === "routine" || selectedFilter === "all") && (
            <p role="alert" className="text-error">{routineFetchError}</p>
        )}
        {hasMatchingPatrols ?
            <>
            {matchingPatrols.map((patrol) => (
            <ProjectPatrolCard
                key={`patrol-${patrol.id}`}
                color="#F97316"
                patrol={patrol}
            />
            ))}
            {matchingRoutinePatrols.map((patrol) => (
                <RoutinePatrolCard key={`routine-${patrol.id}`} patrol={patrol} />
            ))}
            </>
        :
        <div className="w-full flex flex-col justify-center items-center text-secondary-content pt-30">
            <TbMapRoute className="text-4xl"/>
            
            {selectedFilter!=="all" ?
            <h1>This project has no {selectedFilter} patrols</h1>
            :
            <h1>This project has no patrols</h1>
            }
            {props.canManage && <p className="text-sm">Assign a patrol or create one to get started</p>}
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
                    <form onSubmit={(event) => event.preventDefault()}>
                        <fieldset className="fieldset flex-1">
                        <legend className="fieldset-legend font-medium text-secondary-content">PATROL NAME</legend>
                        <input
                            type="text"
                            className="input w-full bg-base-200 border border-white/15 text-base-content"   
                            maxLength={100}
                            value={patrolName}
                            onChange={(event) => setPatrolName(event.target.value)}
                        />
                        </fieldset>

                        <fieldset className="fieldset flex-1">
                        <legend className="fieldset-legend font-medium text-secondary-content">FREQUENCY</legend>
                        <select
                        className="select w-full bg-base-200 border"
                        value={frequency}
                        onChange={(event) => setFrequency(event.target.value)}
                        >
                            <option value="once">Once</option>
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                        </select>
                        </fieldset>

                        <fieldset className="fieldset flex-1">
                        <legend className="fieldset-legend font-medium text-secondary-content">START DATE</legend>
                        <input
                            type="date"
                            className="input w-full bg-base-200 border border-white/15 text-base-content"
                            required
                            value={startDate}
                            onChange={(event) => setStartDate(event.target.value)}
                        />
                        </fieldset>
                    </form>

                </div>

                <div className="rounded-xl bg-base-200 p-6 border mt-4 border-white/8">
                    <h1 className="font-semibold">Route Summary</h1>
                    <div className="grid grid-cols-2 gap-2 mt-4">
                        <CenteredCard>
                            <h1 className="font-semibold">
                                {pathCoordinates.length}
                            </h1>
                            <p className="text-secondary-content text-xs">
                                Waypoints
                            </p>
                        </CenteredCard>
                        <CenteredCard>
                            <h1 className="font-semibold">
                                {formattedDistance}
                            </h1>
                            <p className="text-secondary-content text-xs">
                                Est. Distance
                            </p>
                        </CenteredCard>
                        <CenteredCard>
                            <h1 className="font-semibold">
                                {formattedDuration}
                            </h1>
                            <p className="text-secondary-content text-xs">
                                Est. Duration
                            </p>
                        </CenteredCard>
                        <CenteredCard>
                            <h1 className="font-semibold">
                                {frequency.charAt(0).toUpperCase() + frequency.slice(1)}
                            </h1>
                            <p className="text-secondary-content text-xs">
                                Frequency
                            </p>
                        </CenteredCard>
                    </div>
                    <p className="mt-2 text-secondary-content text-sm text-center">At least two waypoints required</p>
                </div>

                {creationError && (
                    <p role="alert" className="text-error text-sm mt-3">{creationError}</p>
                )}
                <button
                    className="btn btn-primary w-full mt-4"
                    onClick={createRoutinePatrol}
                    disabled={isSavingPatrol || !props.projectID || pathCoordinates.length < 2}
                >
                    {isSavingPatrol ? "Creating..." : "Create Patrol"}
                </button>
            </div>


            <div className="flex-5">
                <div className="flex ml-6 items-center">
                    <button
                        className="btn btn-accent"
                        onClick={autoGeneratePath}
                        disabled={isGeneratingPath || !props.projectID}
                    >
                        <PiMagicWand className="text-xl"/>
                        {isGeneratingPath ? "Generating..." : "Auto-Generate Path"}
                    </button>
                    <button
                        className="btn btn-secondary ml-2"
                        onClick={() => setPathCoordinates([])}
                        disabled={pathCoordinates.length === 0}
                    >
                        <TbTrash className="text-xl" />
                        Clear Path
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
                    pathCoordinates={pathCoordinates}
                    handlePath={setPathCoordinates}
                    />
                </div>

                <div className="rounded-xl bg-base-200 p-6 border border-white/8 ml-6 mt-4">
                    <h1 className="font-semibold">
                        Waypoints
                    </h1>

                    {pathCoordinates.map(([latitude, longitude], index) => (
                        <Waypoint
                            key={`${latitude}-${longitude}-${index}`}
                            count={index + 1}
                            coords={`${latitude.toFixed(6)}°, ${longitude.toFixed(6)}°`}
                            deleteEvent={() => setPathCoordinates((current) =>
                                current.filter((_, waypointIndex) => waypointIndex !== index)
                            )}
                        />
                    ))}
                </div>
            </div>
        </div>
        </>
    }
    </>);
}