"use client"

import { useRef, useState } from "react";
import { FaArrowUp, FaThermometer, FaThermometerEmpty } from "react-icons/fa";
import { FiLayers } from "react-icons/fi";
import { IoIosArrowUp, IoMdWifi } from "react-icons/io";
import GlowButton from "../GlowButton";
import { RxCross2 } from "react-icons/rx";
import dynamic from "next/dynamic";
import type { FeatureGroup as LeafletFeatureGroup } from "leaflet";
import { IoWarning } from "react-icons/io5";
import type { GeoJSON } from 'geojson';
import { Device, IncidentType } from "@/app/home/project/page";
const ForestMapFull = dynamic(() => import("../ForestMapFull"), {
    ssr: false,
});

interface ForestMapViewProps {
    projectID : string | null;
    geoJSON : GeoJSON | null | undefined;
    gridCells : any;
    incidents : IncidentType[];
    devices : Device[];
}

export default function ForestMapView(props: ForestMapViewProps) {
    const [mapTags , setMapTags] = useState({
        incidents : {title : "Incidents", color : "#F87171", active : true, key : "incidents"},
        riskHeatmap : {title : "Risk Heatmap", color : "#F97316", active : true, key : "riskHeatmap"},
        devices : {title : "Devices", color : "#4ADE80", active : true, key : "devices"},
    });
    const [heatmapOpacity, setHeatmapOpacity] = useState<number>(50);
    const [latitude, setLatitude] = useState<number>(52.51);
    const [longitude, setLongitude] = useState<number>(13.38);

    const drawnItemsReference = useRef<LeafletFeatureGroup | null>(null);

    const toggleMapLayer = (index : string, value : boolean) => {
        const newMapTags = {...mapTags};
        newMapTags[index as "incidents"|"riskHeatmap"|"devices"].active = value;
        setMapTags(newMapTags);
    }

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

        <div className="mx-6 mt-2 mb-20">
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
            />
        </div>
</>);
}