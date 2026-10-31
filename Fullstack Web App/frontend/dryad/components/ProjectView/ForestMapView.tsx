"use client"

import { useEffect, useRef, useState } from "react";
import { FaArrowUp, FaBrain, FaThermometer, FaThermometerEmpty } from "react-icons/fa";
import { FiLayers } from "react-icons/fi";
import { IoIosArrowUp, IoMdWifi } from "react-icons/io";
import GlowButton from "../GlowButton";
import { RxCross2 } from "react-icons/rx";
import dynamic from "next/dynamic";
import type { FeatureGroup as LeafletFeatureGroup } from "leaflet";
import { IoWarning } from "react-icons/io5";
import type { GeoJSON } from 'geojson';
import { Device, IncidentType } from "@/app/home/project/page";
import { apiFetch } from "@/library/api";
import { useToast } from "../ToastProvider";
import { useSearchParams } from "next/navigation";
import { PiLightning } from "react-icons/pi";
import { MdLoop } from "react-icons/md";
import { Project } from "@/app/home/projects/new/page";
const ForestMapFull = dynamic(() => import("../ForestMapFull"), {
    ssr: false,
});

interface ForestMapViewProps {
    projectID : string | null;
    geoJSON : GeoJSON | null | undefined;
    gridCells : any;
    setGridCells : (gridCells : any) => void;
    incidents : IncidentType[];
    devices : Device[];
    project : Project;
    canCalculateRisk: boolean;
    routinePatrolId: string | null;
}

export default function ForestMapView(props: ForestMapViewProps) {
    const { showToast } = useToast();
    const [mapTags , setMapTags] = useState({
        incidents : {title : "Incidents", color : "#F87171", active : true, key : "incidents"},
        riskHeatmap : {title : "Risk Heatmap", color : "#F97316", active : true, key : "riskHeatmap"},
        devices : {title : "Devices", color : "#4ADE80", active : false, key : "devices"},
    });
    const [heatmapOpacity, setHeatmapOpacity] = useState<number>(50);
    const [routinePatrolPath, setRoutinePatrolPath] = useState<GeoJSON | null>(null);
    const [routinePatrolError, setRoutinePatrolError] = useState("");

    const searchParams = useSearchParams();
    const lat = searchParams.get('lat');
    const lng = searchParams.get('lng');

    const [latitude, setLatitude] = useState<number | null>(lat!=null ? parseFloat(lat) : lat);
    const [longitude, setLongitude] = useState<number | null>(lng!=null ? parseFloat(lng) : lng);

    const drawnItemsReference = useRef<LeafletFeatureGroup | null>(null);

    useEffect(() => {
        if (!props.projectID || !props.routinePatrolId) {
            setRoutinePatrolPath(null);
            setRoutinePatrolError("");
            return;
        }

        let cancelled = false;
        setRoutinePatrolPath(null);
        setRoutinePatrolError("");

        apiFetch(
            `projects/${props.projectID}/routine_patrols/${props.routinePatrolId}/`
        )
            .then(async (response) => {
                if (!response.ok) throw new Error(await response.text());
                return response.json();
            })
            .then((patrol: { path: GeoJSON }) => {
                if (!cancelled) setRoutinePatrolPath(patrol.path);
            })
            .catch((error) => {
                console.error("Routine patrol map load failed:", error);
                if (!cancelled) setRoutinePatrolError("Unable to load this routine patrol route.");
            });

        return () => {
            cancelled = true;
        };
    }, [props.projectID, props.routinePatrolId]);

    const toggleMapLayer = (index : string, value : boolean) => {
        const newMapTags = {...mapTags};
        newMapTags[index as "incidents"|"riskHeatmap"|"devices"].active = value;
        setMapTags(newMapTags);
    }

    const calculateRisk = () => {
        if (!props.canCalculateRisk) return;

        apiFetch(`projects/${props.projectID}/calculate_risk`,
            {
                method : "POST"
            }
        )
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .then((data)=>{
            props.setGridCells(data)
            showToast(data.message ?? "Risk calculation completed.");
        })
        .catch((err) => {
            console.error("Risk calculation failed:", err);
            showToast("Unable to calculate project risk.", "error");
        });
    }

    let formalDateTime;
    if(props.project.lastTrained){
        const date = new Date(props.project.lastTrained!);
        formalDateTime = date.toLocaleString("en-US");
    }else formalDateTime = "Never"
    

    return (<>
        <div className="flex mx-6 mt-4 items-center">
            <details className="dropdown">
                <summary className="btn border border-accent/50 bg-accent/15 text-accent font-medium">
                    <FiLayers className="text-lg"/>
                    Layers
                    <IoIosArrowUp className="text-lg" />
                </summary>

                <div className="dropdown-content z-[1] card card-compact w-80 p-4 bg-base-200 border border-white/8 rounded-box mt-2">
                    <div className="text-xs font-bold text-secondary-content uppercase mb-4 tracking-wider">
                    Map Layers
                    </div>

                    <div className="flex flex-col gap-4 my-2 divide-y divide-white/8">
                    <div className="flex items-center justify-between pb-4">
                        <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-red-950/50 text-warning text-xl">
                            <IoWarning/>
                        </div>
                        <div>
                            <p className="font-semibold text-sm">Incidents</p>
                            <p className="text-xs text-secondary-content">Past 30 days</p>
                        </div>
                        </div>
                        <input 
                        type="checkbox" 
                        className="toggle toggle-success" 
                        checked={mapTags.incidents.active}
                        onChange={(e)=>toggleMapLayer("incidents", e.target.checked)} />
                    </div>

                    <div className="flex flex-col gap-2 pb-4">
                        <div className="flex items-center justify-between pb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-[#F97316]/15 text-[#F97316] text-xl">
                                <FaThermometerEmpty />
                            </div>
                            <div>
                            <p className="font-semibold text-sm">Risk Heatmap</p>
                            </div>
                        </div>
                        <input type="checkbox" className="toggle toggle-success" checked={mapTags.riskHeatmap.active}
                        onChange={(e)=>toggleMapLayer("riskHeatmap", e.target.checked)} />
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-secondary-content">
                            <span>Opacity</span>
                            <span>{heatmapOpacity}%</span>
                        </div>
                        <input 
                        type="range" 
                        min={0} 
                        max={100} 
                        value={heatmapOpacity} 
                        onChange={(e)=>setHeatmapOpacity(parseInt(e.target.value))} 
                        disabled={!mapTags.riskHeatmap.active}
                        className="range range-primary" />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-accent/15 text-accent text-xl">
                            <IoMdWifi />
                        </div>
                        <div>
                            <p className="font-semibold text-sm">Devices</p>
                        </div>
                        </div>
                        <input type="checkbox" className="toggle toggle-success" checked={mapTags.devices.active}
                        onChange={(e)=>toggleMapLayer("devices", e.target.checked)} />
                    </div>
                    </div>
                </div>
            </details>

            {Object.entries(mapTags)
            .filter(([_, mapTag]) => mapTag.active)
            .map(([key, mapTag]) => {
                return (
                    <GlowButton key={key} 
                    color={mapTag.color} 
                    className="btn-sm ml-2"
                    onClick={()=>toggleMapLayer(mapTag.key, false)}>
                        {mapTag.title}
                        <RxCross2 />
                    </GlowButton>
                );
            })}
        </div>

        <div className="mx-6 mt-2 min-h-120">
            {routinePatrolError && (
                <p role="alert" className="mb-2 text-error">{routinePatrolError}</p>
            )}
            <ForestMapFull 
            latitude={latitude}
            longitude={longitude}
            drawingEnabled={false}
            drawnItemsReference={drawnItemsReference}
            geoJSON={props.geoJSON ?? null}
            gridCells={props.gridCells}
            gridOpacity={mapTags.riskHeatmap.active ? heatmapOpacity/100 : 0}
            incidents={props.incidents}
            enableIncidents={mapTags.incidents.active}
            devices={props.devices}
            enableDevices={mapTags.devices.active}
            routinePatrolPath={routinePatrolPath}
            />
        </div>

        {props.canCalculateRisk && (
        <div className="mx-6 mt-4 border border-white/8 flex justify-between bg-base-200 py-4 px-6 rounded-xl">
            <div>
                <h1 className="font-semibold">
                    Risk Prediction
                </h1>
                <p className="text-secondary-content text-sm">
                    Run the AI model across all monitored sectors to generate a live threat assessment
                </p>
            </div>

            <button className="btn btn-primary"
            onClick={calculateRisk}>
                <PiLightning />
                Calculate Risk
            </button>
        </div>
        )}

        <div className="flex  gap-4 mx-6 mt-4 mb-30">
            <div className="border border-white/8 bg-base-200 py-4 px-6 rounded-xl flex-3">
                <div className="p-2 border border-[#60A5FA]/70 w-10 h-10 rounded-full flex items-center justify-center bg-[#60A5FA]/25">
                    <FaBrain className="my-2 text-xl text-[#60A5FA]"/>
                </div>
                <h1 className="font-semibold my-2 text-xl">
                    How It Works
                </h1>
                <p className="text-secondary-content text-sm">
                    Data obtained from the detection devices is used to train the Risk Prediction Model. The model learns from terrain features (e.g. elevation, slope, proximity to landmarks, etc) and historical attack data.
                    This helps it determine a risk score for each cell of the forest.
                </p>
            </div>
            <div className="border border-white/8 bg-base-200 py-4 px-6 rounded-xl flex-1">
                <div className="p-2 border border-[#F59E0B]/70 w-10 h-10 rounded-full flex items-center justify-center bg-[#F59E0B]/25">
                    <MdLoop className="my-2 text-xl text-[#F59E0B]"/>
                </div>
                <h1 className="font-semibold my-2 text-xl">
                    Training History
                </h1>
                <div className="flex items-end">
                    <h1 className="text-4xl font-bold text-[#F59E0B]">
                        {props.project.trainCount}
                    </h1>
                    <p className="text-secondary-content text-sm ml-2">
                        retraining cycles
                    </p>
                </div>

                <p className="text-secondary-content text-sm mt-2">
                    Last retrained: {formalDateTime}
                </p>
            </div>
        </div>
</>);
}