import { useRef, useState } from "react";
import BottomBar from "./BottomBar";
import dynamic from "next/dynamic";
import { FaSearch } from "react-icons/fa";
import type { GeoJSON } from 'geojson';
import { IoMdCheckmark } from "react-icons/io";
import { RxCross2 } from "react-icons/rx";
import type { LatLng, FeatureGroup as LeafletFeatureGroup } from "leaflet";
import L from "leaflet";
import * as turf from "@turf/turf";

type Waypoint = {
    latitude: string;
    longitude: string;
};

function getWaypoints(geoJSON: GeoJSON | null): Waypoint[] {
    const geometry = geoJSON && "geometry" in geoJSON
        ? geoJSON.geometry
        : geoJSON;

    if (!geometry || geometry.type !== "Polygon") return [];

    const ring = geometry.coordinates[0] ?? [];
    const first = ring[0];
    const last = ring[ring.length - 1];
    const vertices =
        first && last && first[0] === last[0] && first[1] === last[1]
            ? ring.slice(0, -1)
            : ring;

    return vertices.map(([longitude, latitude]) => ({
        latitude: String(latitude),
        longitude: String(longitude),
    }));
}

const ForestMap = dynamic(() => import("../ForestMap"), {
    ssr: false,
});

interface StepPageProps {
    backEvent : ()=>void;
    submitEvent : () => void;
    forestArea : number | null;
    geoJSON : GeoJSON | null;
    handleArea : (geoJSON : GeoJSON | null, area : number | null, center : LatLng | null) => void;
}

export default function StepTwoPage(props: StepPageProps) {
    const [search, setSearch] = useState<string>("");
    const [latitude, setLatitude] = useState<number>(52.51);
    const [longitude, setLongitude] = useState<number>(13.38);
    const [searchSpinner, setSearchSpinner] = useState<boolean>(false);
    const [waypoints, setWaypoints] = useState<Waypoint[]>(
        () => {
            const existingWaypoints = getWaypoints(props.geoJSON);
            return existingWaypoints.length > 0
                ? existingWaypoints
                : Array.from({ length: 3 }, () => ({
                    latitude: "",
                    longitude: "",
                }));
        }
    );
    const [waypointsChanged, setWaypointsChanged] = useState(false);
    const pendingAreaJSON = useRef<string | null>(null);

    const searchLocation = async (e : React.SubmitEvent) => {
        e.preventDefault();
        setSearchSpinner(true);

        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(search)}`
        );

        if (!response.ok){
            setSearchSpinner(false);
            throw new Error(await response.text());
        }

        const data = await response.json();

        if(data.length>0){
            setLatitude(parseFloat(data[0].lat));
            setLongitude(parseFloat(data[0].lon));
        }
        setSearchSpinner(false);
    };

    const handleArea = (area : GeoJSON, areaKMSquare : number, center : LatLng) => {
        setWaypoints(getWaypoints(area));
        setWaypointsChanged(false);
        pendingAreaJSON.current = JSON.stringify(area);
        props.handleArea(area, areaKMSquare, center);
    }

    const drawnItemsReference = useRef<LeafletFeatureGroup | null>(null);

    const clearAllWaypoints = () => {
        setWaypoints([]);
        setWaypointsChanged(false);
        pendingAreaJSON.current = JSON.stringify(null);
        props.handleArea(null, null, null);
        drawnItemsReference.current?.clearLayers();
    }

    const updateWaypoint = (
        index: number,
        key: keyof Waypoint,
        value: string
    ) => {
        setWaypointsChanged(true);
        setWaypoints((current) =>
            current.map((waypoint, waypointIndex) =>
                waypointIndex === index
                    ? { ...waypoint, [key]: value }
                    : waypoint
            )
        );
    };

    const validWaypoints = waypoints.length >= 3 && waypoints.every((waypoint) => {
        if (!waypoint.latitude.trim() || !waypoint.longitude.trim()) return false;

        const latitude = Number(waypoint.latitude);
        const longitude = Number(waypoint.longitude);

        return (
            Number.isFinite(latitude) &&
            latitude >= -90 &&
            latitude <= 90 &&
            Number.isFinite(longitude) &&
            longitude >= -180 &&
            longitude <= 180
        );
    });
    const areaUpdatePending =
        pendingAreaJSON.current !== null &&
        JSON.stringify(props.geoJSON) !== pendingAreaJSON.current;

    const applyWaypoints = () => {
        if (!validWaypoints) return;

        const vertices = waypoints.map((waypoint) => [
            Number(waypoint.longitude),
            Number(waypoint.latitude),
        ]);
        const coordinates = [...vertices, vertices[0]];
        const area = turf.polygon([coordinates]);
        const geoJSON = area as GeoJSON;
        const center = L.geoJSON(geoJSON).getBounds().getCenter();
        const areaKMSquare = Math.round(turf.area(area) / 1_000_000);

        handleArea(geoJSON, areaKMSquare, center);
    };

    return (
    <div className="min-h-[calc(100vh-5rem)] flex flex-col">
        <div className="flex flex-row ml-30 mt-8">
          <p className="text-sm text-secondary-content">Step 2 of 5</p>
          <p className="text-sm text-accent ml-5 font-semibold">Location</p>
        </div>

        <h1 className="pt-3 text-3xl font-bold mx-30">Choose a Forest Location</h1>
        <p className="pt-2 text-secondary-content mx-30">Search or use the map to define the forest area you want to monitor.</p>

        <div className="flex-1 mx-30 mt-2 mb-8 flex flex-col">
            <form className="flex flex-row items-center mb-5" onSubmit={searchLocation}>
                <button 
                    className="btn btn-primary mr-2 w-12"
                    type="submit"
                    disabled={searchSpinner}
                >
                    {searchSpinner ? <span className="loading loading-spinner w-full"></span>: <FaSearch />}
                </button>
                <fieldset className="fieldset flex-1">
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
                drawingEnabled={props.forestArea==null}
                editingEnabled={true}
                drawnItemsReference={drawnItemsReference}
                geoJSON={props.geoJSON}
                />

            <p className="text-secondary-content text-md mt-1">
                *Use the buttons on the top right of the map to draw the area you want to monitor
            </p>

            <section className="mt-5 w-full rounded-xl border border-white/8 bg-base-200 p-4">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <h2 className="font-semibold">Monitoring area waypoints</h2>
                        <p className="text-sm text-secondary-content">
                            Enter at least three latitude and longitude pairs to define the boundary.
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <button
                            type="button"
                            className="btn btn-sm btn-ghost"
                            onClick={() => {
                                setWaypointsChanged(true);
                                setWaypoints((current) => [
                                    ...current,
                                    { latitude: "", longitude: "" },
                                ]);
                            }}
                        >
                            Add waypoint
                        </button>
                        <button
                            type="button"
                            className="btn btn-sm btn-error/10 border border-error/25 text-error"
                            onClick={clearAllWaypoints}
                            disabled={waypoints.length === 0 && props.geoJSON == null}
                        >
                            <RxCross2 />
                            Clear all
                        </button>
                    </div>
                </div>

                <div className="flex flex-col gap-3">
                    {waypoints.map((waypoint, index) => (
                        <div
                            key={index}
                            className="grid grid-cols-[auto_1fr_1fr_auto] items-end gap-3"
                        >
                            <span className="pb-3 text-sm text-secondary-content">
                                {index + 1}
                            </span>
                            <label className="fieldset">
                                <span className="fieldset-legend">Latitude</span>
                                <input
                                    type="number"
                                    min="-90"
                                    max="90"
                                    step="any"
                                    className="input w-full bg-base-100"
                                    aria-label={`Waypoint ${index + 1} latitude`}
                                    placeholder="e.g. -1.2864"
                                    value={waypoint.latitude}
                                    onChange={(event) =>
                                        updateWaypoint(index, "latitude", event.target.value)
                                    }
                                />
                            </label>
                            <label className="fieldset">
                                <span className="fieldset-legend">Longitude</span>
                                <input
                                    type="number"
                                    min="-180"
                                    max="180"
                                    step="any"
                                    className="input w-full bg-base-100"
                                    aria-label={`Waypoint ${index + 1} longitude`}
                                    placeholder="e.g. 36.8172"
                                    value={waypoint.longitude}
                                    onChange={(event) =>
                                        updateWaypoint(index, "longitude", event.target.value)
                                    }
                                />
                            </label>
                            <button
                                type="button"
                                className="btn btn-square btn-ghost mb-1"
                                aria-label={`Remove waypoint ${index + 1}`}
                                onClick={() => {
                                    setWaypointsChanged(true);
                                    setWaypoints((current) =>
                                        current.filter((_, waypointIndex) => waypointIndex !== index)
                                    );
                                }}
                            >
                                <RxCross2 />
                            </button>
                        </div>
                    ))}
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-secondary-content">
                        {waypointsChanged
                            ? validWaypoints
                            ? `${waypoints.length} valid waypoints`
                            : "Enter valid coordinates for at least three waypoints."
                            : "Waypoint values match the current boundary."}
                    </p>
                    <button
                        type="button"
                        className="btn btn-primary"
                        onClick={applyWaypoints}
                        disabled={!validWaypoints}
                    >
                        Apply waypoints
                    </button>
                </div>
            </section>

            {props.forestArea!=null &&
            <div className="mt-5 w-full flex flex-row items-center bg-base-300 p-4 rounded-xl border border-white/8">
                <div className="bg-primary rounded-full mr-4">
                    <IoMdCheckmark className="text-xl m-3"/>
                </div>
                <div>
                    <h1 className="text-lg font-semibold text-accent">Area Selected ({props.forestArea}km²)</h1>
                    <p className="text-sm text-secondary-content">Continue to the next step, or update the area using the map or waypoints.</p>
                </div>
            </div>}
        </div>

        <BottomBar ready={props.geoJSON!=null && !waypointsChanged && !areaUpdatePending} next="Continue" back="Back" formID="project-form" backEvent={props.backEvent} nextEvent={props.submitEvent}/>
    </div>);
}