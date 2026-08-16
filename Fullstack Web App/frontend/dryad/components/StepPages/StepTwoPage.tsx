import { useRef, useState } from "react";
import BottomBar from "./BottomBar";
import dynamic from "next/dynamic";
import { FaSearch } from "react-icons/fa";
import type { GeoJSON } from 'geojson';
import * as turf from "@turf/turf";
import { IoMdCheckmark } from "react-icons/io";
import { RxCross2 } from "react-icons/rx";
import type { FeatureGroup as LeafletFeatureGroup } from "leaflet";

const ForestMap = dynamic(() => import("../ForestMap"), {
    ssr: false,
});

interface StepPageProps {
    backEvent : ()=>void;
    submitEvent : () => void;
    // nameValue : string;
    // descriptionValue : string;
    // colorValue : string;
    // nameFunction : (e : React.ChangeEvent<HTMLInputElement>) => void;
    // descriptionFunction : (e : React.ChangeEvent<HTMLTextAreaElement>) => void;
    // colorFunction : (e : React.ChangeEvent<HTMLInputElement>) => void;
}

export default function StepTwoPage(props: StepPageProps) {
    const [search, setSearch] = useState<string>("");
    const [latitude, setLatitude] = useState<number>(52.51);
    const [longitude, setLongitude] = useState<number>(13.38);
    const [searchSpinner, setSearchSpinner] = useState<boolean>(false);
    const [forestGeoJSON, setForestGeoJSON] = useState<GeoJSON | null>();
    const [forestArea, setForestArea] = useState<number | null>();

    const searchLocation = async (e : React.SubmitEvent) => {
        e.preventDefault();
        setSearchSpinner(true);

        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(search)}`
        );

        const data = await response.json();

        if(data.length>0){
            setLatitude(parseFloat(data[0].lat));
            setLongitude(parseFloat(data[0].lon));
        }
        setSearchSpinner(false);
    };

    const handleArea = (area : GeoJSON) => {
        setForestGeoJSON(area);
        const areaKMSquare = Math.round(turf.area(area)/1_000_000);
        setForestArea(areaKMSquare);
    }

    const drawnItemsReference = useRef<LeafletFeatureGroup | null>(null);

    const resetForestArea = () => {
        setForestArea(null);
        setForestGeoJSON(null);
        drawnItemsReference.current?.clearLayers();
    }

    return (
    <div className="h-[calc(100vh-5rem)] flex flex-col">
        <div className="flex flex-row ml-30 mt-8">
          <p className="text-sm text-secondary-content">Step 2 of 5</p>
          <p className="text-sm text-accent ml-5 font-semibold">Location</p>
        </div>

        <h1 className="pt-3 text-3xl font-bold mx-30">Choose a Forest Location</h1>
        <p className="pt-2 text-secondary-content mx-30">Search or use the map to define the forest area you want to monitor.</p>

        <div className="flex-1 mx-30 mt-2 mb-20 flex flex-col">
            <form className="flex flex-row items-center mb-5" onSubmit={searchLocation}>
                <button 
                    className="btn btn-primary mr-2 w-12"
                    type="submit"
                    disabled={searchSpinner}
                >
                    {searchSpinner ? <span className="loading loading-spinner w-full"></span>: <FaSearch />}
                </button>
                <fieldset className="fieldset flex-1">
                    {/* <legend className="fieldset-legend font-medium text-secondary-content text-xs">Search Location</legend> */}
                    <input 
                    type="text"
                    className="input w-full bg-base-200 border"
                    placeholder="Search forests, regions, countries"
                    value={search}
                    onChange={(e)=>setSearch(e.target.value)}/>
                </fieldset>
            </form>

            <ForestMap 
                searchValue={search}
                latitude={latitude}
                longitude={longitude}
                handleArea={handleArea}
                drawingEnabled={forestArea==null}
                drawnItemsReference={drawnItemsReference}
                />

            <p className="text-secondary-content text-md mt-1">
                *Use the buttons on the top right of the map to draw the area you want to monitor
            </p>

            {forestArea!=null ?
            <div className="mt-5 w-full flex flex-row items-center bg-base-300 p-4 rounded-xl border border-white/8">
                <div className="bg-primary rounded-full mr-4">
                    <IoMdCheckmark className="text-xl m-3"/>
                </div>
                <div>
                    <h1 className="text-lg font-semibold text-accent">Area Selected ({forestArea}km²)</h1>
                    <p className="text-sm text-secondary-content">You can proceed to the next step, or clear and choose a different area.</p>
                </div>

                <button className="btn btn-error/10 ml-auto text-error border border-error/25"
                    onClick={resetForestArea}>
                    <RxCross2 className="text-error"/>
                    Clear Selection
                </button>
            </div>:<></>}
        </div>

        <BottomBar next="Continue" back="Back" formID="project-form" backEvent={props.backEvent} nextEvent={props.submitEvent}/>
    </div>);
}