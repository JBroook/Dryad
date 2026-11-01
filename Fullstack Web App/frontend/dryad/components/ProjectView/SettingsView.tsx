"use client"

import { Project, ThreatClass } from "@/app/home/projects/new/page";
import { apiFetch } from "@/library/api";
import { useEffect, useRef, useState } from "react";
import { FaRegTrashAlt, FaSave, FaSearch } from "react-icons/fa";
import ThreatClassOption from "../ThreatClassOption";
import { IoPower } from "react-icons/io5";
import type { GeoJSON } from 'geojson';
import type { LatLng, FeatureGroup as LeafletFeatureGroup } from "leaflet";
import { IoMdCheckmark } from "react-icons/io";
import { RxCross2 } from "react-icons/rx";
import dynamic from "next/dynamic";
import { useToast } from "../ToastProvider";
import { useRouter } from "next/navigation";
import { MdOutlineExitToApp } from "react-icons/md";

const ForestMap = dynamic(() => import("../ForestMap"), {
    ssr: false,
});

interface SettingsViewProps {
    projectID : string | null;
    canEdit: boolean;
    isOwner: boolean;
}


export default function SettingsView(props: SettingsViewProps) {
    const { showToast } = useToast();
    const router = useRouter();
    const [project, setProject] = useState<Project | null>();
    const [threatClasses, setThreatClasses] = useState<ThreatClass[]>([]);
    const [search, setSearch] = useState<string>("");
    const [latitude, setLatitude] = useState<number>(52.51);
    const [longitude, setLongitude] = useState<number>(13.38);
    const [searchSpinner, setSearchSpinner] = useState<boolean>(false);
    const [saveSpinner, setSaveSpinner] = useState<boolean>(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [leaveSpinner, setLeaveSpinner] = useState<boolean>(false);

    const extractProjectFeatures = (data : any) => {
        setProject({
            ...data.properties,
            area : data.properties.surface_area,
            id : data.id,
            geoJSON : data.geometry,
            trainCount : data.properties.train_count,
            lastTrained : data.properties.last_trained,
            threatClasses : data.properties.threat_classes,
            confidenceThreshold : data.properties.confidence_threshold,
            alertPreference : data.properties.alert_recipients
        })
    }

    const toggleThreatClass = (index : number) => {
        const newThreatClasses = [...threatClasses]
        newThreatClasses[index].active = !newThreatClasses[index].active
        setThreatClasses(newThreatClasses)
    }

    const openModal = (id : string)=>{
        const modal = document.getElementById(id) as HTMLDialogElement;
        modal.showModal();
    }

    const closeModal = (id : string) => {
        const modal = document.getElementById(id) as HTMLDialogElement;
        modal.close();
    }

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

    const handleArea = async (geoJSON : GeoJSON | null, area : number | null, center : LatLng | null)=>{
        let newRegion = null;
        if(geoJSON){
            const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${center?.lat}&lon=${center?.lng}&format=jsonv2`
            );
            const data = await response.json();
            newRegion = `${data.address.state}, ${data.address.country}`
        }
        setProject(currentProject => {
            if (!currentProject) return currentProject;
            return {
                ...currentProject,
                area : area,
                geoJSON : geoJSON,
                region : newRegion,
                center : center
            };
        });
    }
    
    const drawnItemsReference = useRef<LeafletFeatureGroup | null>(null);

    const resetForestArea = () => {
        handleArea(null, null, null);
        drawnItemsReference.current?.clearLayers();
    }

    const saveChanges = async () => {
        if (!props.canEdit || !project || !props.projectID || saveSpinner) return;

        if (!project.geoJSON || project.area == null) {
            setSaveError("Select a monitoring area before saving project changes.");
            return;
        }

        const monitoringArea =
            "geometry" in project.geoJSON
                ? project.geoJSON.geometry
                : project.geoJSON;

        setSaveSpinner(true);
        setSaveError(null);

        try {
            const response = await apiFetch(
                `projects/${props.projectID}/`,
                {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        name: project.name,
                        description: project.description,
                        color: project.color,
                        surface_area: project.area,
                        region: project.region,
                        confidence_threshold: project.confidenceThreshold,
                        alert_recipients: project.alertPreference,
                        monitoring_area: monitoringArea,
                        ...(project.center
                            ? {
                                  coordinates: `${project.center.lat},${project.center.lng}`,
                              }
                            : {}),
                        threat_classes: threatClasses
                            .filter((threatClass) => threatClass.active)
                            .map((threatClass) => ({
                                id: threatClass.id,
                                threat_class_id: threatClass.id,
                            })),
                    }),
                }
            );

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || "Unable to save project changes.");
            }

            const data = await response.json();
            showToast(data.message ?? "Project changes saved successfully.");
        } catch (error) {
            showToast("Unable to save project changes.", "error");
            setSaveError(
                error instanceof Error
                    ? error.message
                    : "Unable to save project changes."
            );
        } finally {
            setSaveSpinner(false);
        }
    };

    const updateProjectStatus = async (event: React.SubmitEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!props.projectID || !project) return;

        const status = !project.status;

        try {
            const response = await apiFetch(
                `projects/${props.projectID}/`,
                {
                    method: "PATCH",
                    body: JSON.stringify({ status }),
                }
            );
            if (!response.ok) throw new Error(await response.text());
            const data = await response.json();
            setProject((currentProject) =>
                currentProject ? { ...currentProject, status } : currentProject
            );
            showToast(data.message ?? `Project ${status ? "activated" : "disabled"} successfully.`);
            closeModal("statusModal");
        } catch (error) {
            console.error("Project status update failed:", error);
            showToast(`Unable to ${status ? "activate" : "disable"} this project.`, "error");
        }
    };

    const deleteProject = async (event: React.SubmitEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!props.projectID) return;

        try {
            const response = await apiFetch(
                `projects/${props.projectID}/`,
                { method: "DELETE" }
            );
            if (!response.ok) throw new Error(await response.text());
            const data = await response.json();
            showToast(data.message ?? "Project deleted successfully.");
            closeModal("deleteModal");
            router.push("/home/projects");
        } catch (error) {
            console.error("Project deletion failed:", error);
            showToast("Unable to delete this project.", "error");
        }
    };

    const leaveProject = async (event: React.SubmitEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!props.projectID || leaveSpinner) return;

        setLeaveSpinner(true);
        try {
            const currentUserID = Number(localStorage.getItem("userID"));
            const membersResponse = await apiFetch(
                `projects/${props.projectID}/members`
            );
            if (!membersResponse.ok) {
                throw new Error(await membersResponse.text());
            }

            const members = await membersResponse.json();
            const ownMembership = members.find(
                (membership: { user: { id: number }; accepted: boolean }) =>
                    membership.user.id === currentUserID && membership.accepted
            );
            if (!ownMembership) {
                throw new Error("Your accepted project membership could not be found.");
            }

            const response = await apiFetch(
                `projects/${props.projectID}/members/${ownMembership.id}/`,
                { method: "DELETE" }
            );
            if (!response.ok) throw new Error(await response.text());

            const data = await response.json();
            closeModal("leaveModal");
            showToast(data.message ?? "You left the project successfully.");
            router.push("/home/projects");
        } catch (error) {
            console.error("Project leave failed:", error);
            showToast(
                error instanceof Error ? error.message : "Unable to leave this project.",
                "error"
            );
        } finally {
            setLeaveSpinner(false);
        }
    };

    useEffect(() => {
        if (!props.projectID) return;

        let cancelled = false;

        async function load() {
            try {
                const [projectRes, threatClassesRes] = await Promise.all([
                    apiFetch(`projects/${props.projectID}`),
                    apiFetch("threat_classes/"),
                ]);

                if (!projectRes.ok) throw new Error(await projectRes.text());
                if (!threatClassesRes.ok) throw new Error(await threatClassesRes.text());

                const [projectData, allThreatClasses] = await Promise.all([
                    projectRes.json(),
                    threatClassesRes.json(),
                ]);

                if (cancelled) return;

                extractProjectFeatures(projectData);

                const activeIds = new Set(
                    projectData.properties.threat_classes.map(
                        (item: { threat_class_id: number }) => item.threat_class_id
                    )
                );

                setThreatClasses(
                    allThreatClasses.map((threatClass: ThreatClass) => ({
                        ...threatClass,
                        active: activeIds.has(threatClass.id),
                    }))
                );
            } catch (err) {
                console.error("Fetch failed:", err);
            }
        }

        load();

        return () => {
            cancelled = true;
        };
    }, [props.projectID])
    
    if (project!=null){
        return (
        <>
        {!props.canEdit && (
            <p className="alert mx-6 mt-4" role="status">
                Project settings are read-only for your role.
            </p>
        )}
        <fieldset disabled={!props.canEdit} className="contents">
        <dialog id="statusModal" className="modal">
            <div className="modal-box bg-base-200 border border-white/8">
                <h3 className="font-bold text-lg">
                    {project.status ? "Disable Project" : "Activate Project"}
                </h3>
                <p className="py-4 text-sm text-secondary-content">
                    {project.status
                        ? "This will mark the project as inactive. You can activate it again later."
                        : "This will mark the project as active again."}
                </p>
                <div className="modal-action">
                <form onSubmit={updateProjectStatus}>
                    <button type="submit" className={`btn ${project.status ? "btn-warning" : "btn-primary"} mr-2`}>
                        {project.status ? "Disable" : "Activate"}
                    </button>
                    <button 
                    type="button"
                    onClick={() => closeModal("statusModal")} className="btn btn-secondary">Close</button>
                </form>
                </div>
            </div>
        </dialog>

        <dialog id="deleteModal" className="modal">
            <div className="modal-box bg-base-200 border border-white/8">
                <h3 className="font-bold text-lg">Delete Project</h3>
                <p className="py-4 text-sm text-secondary-content">
                    Deleting this project is a <strong>permanent</strong> action. All data related to this project will be forever lost.
                    <br /><br />
                    Did you mean to <strong>disable</strong> the project instead?
                </p>
                <div className="modal-action">
                <form onSubmit={deleteProject}>
                    <button type="submit" className="btn btn-error mr-2">Delete</button>
                    <button 
                    type="button"
                    onClick={() => closeModal("deleteModal")} className="btn btn-secondary">Close</button>
                </form>
                </div>
            </div>
        </dialog>

        <div className="mt-6 mx-60">
            <div className="card bg-base-200 rounded-2xl border border-white/8">
                <div className="card-body">
                    <h2 className="card-title">Project Identity</h2>

                    <form className="pt-2 flex-1">
                        <fieldset className="fieldset">
                            <legend className="fieldset-legend font-medium text-secondary-content">Project Name</legend>
                            <input
                            type="text"
                            className="input w-full bg-base-200 border"
                            placeholder="e.g. Amazon Shield"
                            value={project.name}
                            onChange={(e)=>setProject({...project, name : e.target.value})}
                            />
                        </fieldset>

                        <fieldset className="fieldset pt-2">
                            <legend className="fieldset-legend font-medium text-secondary-content">Description</legend>
                            <textarea
                            className="textarea w-full bg-base-200 border resize-none"
                            placeholder="Briefly describe what this project is protecting and why it matters"
                            value={project.description}
                            onChange={(e)=>setProject({...project, description : e.target.value})}
                            />
                        </fieldset>

                        <fieldset className="fieldset pt-2">
                            <legend className="fieldset-legend font-medium text-secondary-content">Pick a Color</legend>
                            <input type="color"
                            className="w-32 h-12 p-1 rounded-lg bg-base-200 border border-base-300 cursor-pointer"
                            value={project.color}
                            onChange={(e)=>setProject({...project, color : e.target.value})}
                            >
                            </input>
                        </fieldset>
                    </form>
                </div>
            </div>

            <div className="card bg-base-200 rounded-2xl border border-white/8 mt-4">
                <div className="card-body">
                    <h2 className="card-title">Detection & Alerts</h2>

                    <form className="flex-1">
                        <div className="flex flex-row w-full">
                            <fieldset className="fieldset pt-2 flex-1 mr-2">
                                <legend className="fieldset-legend font-medium text-secondary-content">Confidence Threshold (%)</legend>
                                
                                <input
                                type="number"
                                min="1" max="99"
                                className="input w-full bg-base-200 border"
                                placeholder="e.g. 75"
                                value={project.confidenceThreshold}
                                onChange={(e)=>setProject({...project, confidenceThreshold : parseInt(e.target.value)})}
                                />
                            </fieldset>
        
                            <fieldset className="fieldset pt-2 flex-1 ml-2">
                                <legend className="fieldset-legend font-medium text-secondary-content">Alert Preference</legend>
                                
                                <select 
                                className="select w-full bg-base-200 border"
                                value={project.alertPreference}
                                onChange={(e)=>setProject({...project, alertPreference : e.target.value})}
                                >
                                    <option value="all">All</option>
                                    <option value="managers and up">Managers and above</option>
                                    <option value="admins and up">Admins and above</option>
                                    <option value="owner only">Owner only</option>
                                </select>
                            </fieldset>
                        </div>
        
                        <fieldset className="fieldset pt-2">
                            <legend className="fieldset-legend font-medium text-secondary-content">Threat Classes</legend>
        
                            <div className="w-full">
                                {threatClasses.map((threatClass, index)=>{
                                    return <ThreatClassOption 
                                        key={index}
                                        setActive={()=>toggleThreatClass(index)}
                                        disabled={!props.canEdit}
                                        name={threatClass.name}
                                        description={threatClass.description}
                                        active={threatClass.active}
                                    />
                                })}
        
                                <p className="text-secondary-content text-sm"><i>Select the types of audio that you want Dryad to look out for</i></p>
                            </div>
                        </fieldset>
                    </form>
                </div>
            </div>

            <div className="card bg-base-200 rounded-2xl border border-white/8 mt-4 p-4">
                <form className="flex flex-row items-center mb-4" onSubmit={searchLocation}>
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
                        onChange={(e)=>setSearch(e.target.value)}
                    />
                    </fieldset>
                </form>

                <ForestMap 
                    searchValue={search}
                    latitude={latitude}
                    longitude={longitude}
                    handleArea={handleArea}
                    drawingEnabled={props.canEdit && project.area==null}
                    editingEnabled={props.canEdit}
                    drawnItemsReference={drawnItemsReference}
                    geoJSON={project.geoJSON}
                />

                {props.canEdit && <p className="text-secondary-content text-md mt-1">
                    *Use the buttons on the top right of the map to draw the area you want to monitor
                </p>}

                {project.area!=null ?
                <div className="mt-5 w-full flex flex-row items-center bg-base-300 p-4 rounded-xl border border-white/8">
                    <div className="bg-primary rounded-full mr-4">
                        <IoMdCheckmark className="text-xl m-3"/>
                    </div>
                    <div>
                        <h1 className="text-lg font-semibold text-accent">Area Selected ({project.area}km²)</h1>
                        <p className="text-sm text-secondary-content">You can proceed to the next step, or clear and choose a different area.</p>
                    </div>

                    {props.canEdit && <button className="btn btn-error/10 ml-auto text-error border border-error/25"
                        onClick={resetForestArea}>
                        <RxCross2 className="text-error"/>
                        Clear Selection
                    </button>}
                </div>:<></>}
            </div>
        </div>
        </fieldset>

        <div className="mt-6 mx-60">
            <div className="flex gap-2 items-center mt-4 mb-20">
                {props.canEdit && <button
                    type="button"
                    className="btn btn-primary"
                    onClick={saveChanges}
                    disabled={saveSpinner}
                >
                    {saveSpinner ? (
                        <span className="loading loading-spinner loading-sm" />
                    ) : (
                        <FaSave />
                    )}
                    {saveSpinner ? "Saving..." : "Save Changes"}
                </button>}

                {props.isOwner && <button
                    type="button"
                    className={project.status ? "btn btn-warning" : "btn btn-primary"}
                    onClick={()=>openModal("statusModal")}
                >
                    <IoPower/> {project.status ? "Disable Project" : "Activate Project"}
                </button>}

                {props.isOwner && <button className="btn btn-error" onClick={()=>openModal("deleteModal")}>
                    <FaRegTrashAlt/> Delete Project
                </button>}

                {!props.isOwner && <button
                    type="button"
                    className="btn btn-error"
                    onClick={()=>openModal("leaveModal")}
                >
                    <MdOutlineExitToApp /> Leave Project
                </button>
                }
            </div>
            {saveError && (
                <p role="alert" className="text-error -mt-16 mb-20">
                    {saveError}
                </p>
            )}
        </div>
        <dialog id="leaveModal" className="modal">
            <div className="modal-box bg-base-200 border border-white/8">
                <h3 className="font-bold text-lg">Leave Project</h3>
                <p className="py-4 text-sm text-secondary-content">
                    Are you sure you want to leave the project? You will not be able to access this project again unless you are invited back by a member.
                </p>
                <div className="modal-action">
                <form onSubmit={leaveProject}>
                    <button type="submit" className="btn btn-error mr-2" disabled={leaveSpinner}>
                        {leaveSpinner ? "Leaving..." : "Leave"}
                    </button>
                    <button
                    type="button"
                    onClick={() => closeModal("leaveModal")} className="btn btn-secondary">
                        Close
                    </button>
                </form>
                </div>
            </div>
        </dialog>
    </>);
    }else{
        return (<div className="w-full h-screen flex justify-center items-center">
            <span className="loading loading-spinner"></span>
        </div>)
    }
}