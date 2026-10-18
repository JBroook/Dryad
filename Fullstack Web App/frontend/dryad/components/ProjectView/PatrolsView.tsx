"use client"

import { Patrol, SerializedPatrolMember } from "@/app/home/patrols/page";
import ToggleGlowButton from "../ToggleGlowButton";
import PatrolCard from "../PatrolCard";
import { TbMapRoute } from "react-icons/tb";
import { useEffect, useState } from "react";
import { apiFetch } from "@/library/api";
import ProjectPatrolCard from "../ProjectPatrolCard";
import { FaPlus } from "react-icons/fa";

interface DevicesViewProps {
    projectID : string | null;
}


export default function DevicesView(props: DevicesViewProps) {
    const [patrols, setPatrols] = useState<Patrol[]>([]);
    const [filterIndex, setFilterIndex] = useState<number>(1);
    const filterOptions = [
    {title : "All", key : "all", count : patrols.length},
    {title : "Pending", key : "pending", count : patrols.reduce((count, patrol)=> {return patrol.status === "pending" ? (count + 1) : count}, 0)},
    {title : "Completed", key : "completed", count : patrols.reduce((count, patrol)=> {return patrol.status === "completed" ? (count + 1) : count}, 0)},
    {title : "Cancelled", key : "cancelled", count : patrols.reduce((count, patrol)=> {return patrol.status === "cancelled" ? (count + 1) : count}, 0)},
  ]
  
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
        // fetch project patrols
        apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/patrols/`)
          .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
          })
          .then((data)=>{console.log(data); return data})
          .then((data)=>extractPatrols(data))
          .catch((err) => console.error("Fetch failed:", err));
      },[])
    
      let matchingPatrols = patrols;
    
      if(filterIndex!=0){
        matchingPatrols = patrols.filter(patrol => patrol.status===filterOptions[filterIndex].key)
      }
    
    return (<>
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
            {patrols.length} patrols
        </p>
        <button className="btn btn-primary ml-2">
            <FaPlus/> New Patrol    
        </button>
    </div>

    <div className="mx-6 mt-5">
      {matchingPatrols.length>0 ?
        matchingPatrols.map((patrol, index)=>{
          return <ProjectPatrolCard
            key={index}
            color="#F97316"
            patrol={patrol}
            cancelPatrol={()=>{}}
          />
      })
      :
      <div className="w-full flex flex-col justify-center items-center text-secondary-content pt-30">
        <TbMapRoute className="text-4xl"/>
        
        {filterOptions[filterIndex].key!=="all" ? 
          <h1>This project has no {filterOptions[filterIndex].key} patrols</h1>
          :
          <h1>This project has no patrols</h1>
        }
        <p className="text-sm">Assign a patrol or create one to get started</p>
      </div>
      }
  </div>
    </>);
}