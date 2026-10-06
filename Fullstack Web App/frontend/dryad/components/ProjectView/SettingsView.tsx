"use client"

import { Project, ThreatClass } from "@/app/home/projects/new/page";
import { apiFetch } from "@/lib/api";
import { useEffect, useState } from "react";
import { FaRegTrashAlt, FaSave } from "react-icons/fa";
import ThreatClassOption from "../ThreatClassOption";
import { IoPower } from "react-icons/io5";

interface SettingsViewProps {
    projectID : string | null;
}


export default function SettingsView(props: SettingsViewProps) {
    const [project, setProject] = useState<Project | null>();
    const [threatClasses, setThreatClasses] = useState<ThreatClass[]>([]);

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

    useEffect(() => {
        if (!props.projectID) return;

        let cancelled = false;

        async function load() {
            try {
                const [projectRes, threatClassesRes] = await Promise.all([
                    apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}`),
                    apiFetch("http://127.0.0.1:8000/api/threat_classes/"),
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
        return (<div className="mt-6 mx-60">
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

            <div className="flex gap-2 items-center mt-4 mb-20">
                <button className="btn btn-primary">
                    <FaSave/> Save Changes
                </button>

                <button className="btn btn-warning">
                    <IoPower/> Disable Project
                </button>

                <button className="btn btn-error">
                    <FaRegTrashAlt/> Delete Project
                </button>
            </div>
        </div>);
    }else{
        return (<div className="w-full h-screen flex justify-center items-center">
            <span className="loading loading-spinner"></span>
        </div>)
    }
}