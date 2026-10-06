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

interface OverviewViewProps {
    project : Project;
}

export default function OverviewView(props: OverviewViewProps) {
    const [activityChartData, setActivityChartData] = useState([]);
    const [incidents, setIncidents] = useState<IncidentType[]>([]);

    // const newIncidents = props.incidents?.reduce((count, incident) => {
    //     return incident.status==="new" ? count + 1 : count;
    // }, 0)
    // const onlineDevices = props.devices?.reduce((count, device) => {
    //     return device.status==="online" ? count + 1 : count;
    // }, 0)

    const [overviewCards, setOverviewCards] = useState([
        {title : "Total Incidents", number : 0, color : "#A78BFA"},
        {title : "New Incidents", number : 0, color : "#F87171"},        
        {title : "Online Devices", number : 0, color : "#60A5FA"},
        {title : "Team Members", number : 0, color : "#4ADE80"},        
    ])

    const extractIncidents = (data : any)=>{
        setIncidents(data.filter((incident : IncidentType)=>(incident.status==="new" || incident.status==="reviewing"))
            .map((incident : any)=>{
            return {...incident, 
                threatClass : incident.threat_class,
                coordinates : {
                lat : parseFloat(incident.coordinates.coordinates[0]),
                lng : parseFloat(incident.coordinates.coordinates[1])
                }
            }
        }))
    }

    useEffect(()=>{
        // fetch activity chart data
        apiFetch(`http://127.0.0.1:8000/api/projects/${props.project.id}/incident_activity`)
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .then((data)=>setActivityChartData(data))
        .catch((err) => console.error("Fetch failed:", err));

        // fetch project incidents
        apiFetch(`http://127.0.0.1:8000/api/incidents?project=${props.project.id}`)
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .then((data)=>extractIncidents(data))
        .catch((err) => console.error("Fetch failed:", err));

        // fetch overview info
        apiFetch(`http://127.0.0.1:8000/api/projects/overview?project_id=${props.project.id}`)
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .then((data)=>{console.log(data); return data})
        .then((data)=>{
            const newOverviewCards = [...overviewCards]
            newOverviewCards[0].number = data.total_incidents
            newOverviewCards[1].number = data.new_alerts
            newOverviewCards[2].number = data.online_devices
            newOverviewCards[3].number = data.member_count
            setOverviewCards(newOverviewCards)
        })
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
                    {incidents.length>0 ?
                        incidents.map((incident, index)=>{
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