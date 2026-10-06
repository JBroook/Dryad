"use client"

import { useEffect, useState } from "react";
import HollowCard from "../HollowCard";
import { apiFetch } from "@/lib/api";
import { Member, Project } from "@/app/home/projects/new/page";
import { Device, IncidentType } from "@/app/home/project/page";
import ActivityChart from "../ActivityChart";

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
            <ActivityChart />
        </main>
    </>);
}