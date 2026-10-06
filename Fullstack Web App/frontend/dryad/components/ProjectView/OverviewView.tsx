"use client"

import { useEffect, useState } from "react";
import HollowCard from "../HollowCard";
import { apiFetch } from "@/lib/api";
import { Member, Project } from "@/app/home/projects/new/page";
import { Device, IncidentType } from "@/app/home/project/page";
import ActivityChart from "../ActivityChart";
import Link from "next/link";
import { FaArrowRight, FaPlus } from "react-icons/fa6";
import Incident from "../Incident";
import { IoIosWarning } from "react-icons/io";

interface ProjectStatCard {
  title: string;
  number: number | null;
  color: string;
}

interface OverviewViewProps {
    project : Project;
    incidents : IncidentType[];
    members : Member[];
    devices : Device[];
}

export default function OverviewView(props: OverviewViewProps) {
    const [activityChartData, setActivityChartData] = useState([]);

    const newIncidents = props.incidents?.reduce((count, incident) => {
        return incident.status==="new" ? count + 1 : count;
    }, 0)
    const onlineDevices = props.devices?.reduce((count, device) => {
        return device.status==="online" ? count + 1 : count;
    }, 0)

    const overviewCards = [
        {title : "Total Incidents", number : props.incidents?.length, color : "#A78BFA"},
        {title : "New Incidents", number : newIncidents, color : "#F87171"},        
        {title : "Online Devices", number : onlineDevices, color : "#60A5FA"},
        {title : "Team Members", number : props.members?.length, color : "#4ADE80"},        
    ]

    useEffect(()=>{
        // fetch activity chart data
        apiFetch(`http://127.0.0.1:8000/api/projects/${props.project.id}/incident_activity`)
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .then((data)=>{console.log(data); return data})
        .then((data)=>setActivityChartData(data))
        .catch((err) => console.error("Fetch failed:", err));
    },[])
    
    return (<>
        <div className="w-full grid grid-cols-4 gap-4 px-8 mt-8">
            {overviewCards.map((card, index)=>{
                return (<HollowCard key={index}>
                <div className="stat">
                    {card.number!==null ?
                        <div className="stat-value" style={{color : card.color}}>{card.number}</div>
                        :
                        <span className="loading loading-spinner"></span>
                    }
                    <div className="stat-title">{card.title}</div>
                </div>
                </HollowCard>);
            })}
        </div>

        <main className="p-6">
            <ActivityChart data={activityChartData}/>
        </main>

        <div className="card bg-base-200 rounded-2xl border border-white/8 mx-6 mb-20">
            <div className="card-body">
                <div className="flex justify-between">
                    <h2 className="card-title">Pending Incidents</h2>
                    <Link className="flex items-center gap-2 text-accent" href={`/home/project?pid=${props.project.id}&tab=incidents`}>View All <FaArrowRight/></Link>
                </div>
                
                <div className="mt-4">
                    {props.incidents.length>0 ?
                        props.incidents.map((incident, index)=>{
                            return <Incident
                                key={incident.id}
                                name={incident.threatClass.name}
                                coordinates={incident.coordinates}
                                timestamp={incident.timestamp}
                                device={incident.device?.name ?? "Non-device"}
                                confidence={incident.confidence}
                                status={incident.status}
                                projectID={props.project.id}
                                mini={true}
                            />
                        })
                        :
                        <div className="w-full flex flex-col justify-center items-center text-secondary-content pt-4">
                            <IoIosWarning className="text-4xl"/>
                            <h1>No incidents found</h1>
                        </div>
                    }
                </div>
            </div>
        </div>
    </>);
}