"use client"

import PatrolCard from "@/components/PatrolCard";
import ToggleGlowButton from "@/components/ToggleGlowButton";
import { apiFetch } from "@/lib/api";
import { useEffect, useState } from "react";
import { IncidentType } from "../project/page";

export type Patrol = {
  id : number;
  incident : IncidentType;
  target : { type : string; coordinates : number[]};
  member : number;
  project : number;
}

export default function Patrols() {
  const [patrols, setPatrols] = useState<Patrol[]>([]);
  const [filterIndex, setFilterIndex] = useState<number>(1);

  const filterOptions = [
    "All",
    "Pending",
    "Completed",
    "Cancelled"
  ]
  
  const extractPatrols = (data : any)=>{
    setPatrols(data.map((patrol : any)=>{
      const incident = patrol.incident;
      return {...patrol,
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
    // fetch project incidents
    apiFetch(`http://127.0.0.1:8000/api/users/${1}/patrols/`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>{console.log(data); return data})
      .then((data)=>extractPatrols(data))
      .catch((err) => console.error("Fetch failed:", err));
  },[])

  return (<>
    <div className="w-full py-5 pl-8 border-b-white/8 border-b border-b-width-[2px] flex flex-row items-center justify-between ">
      <div>
        <h1 className="font-bold text-2xl">
          My Patrols
        </h1>
        <p className="text-sm text-secondary-content">
          Field patrols dispatched to you
        </p>
      </div>
    </div>

    <div className="flex gap-2 mx-6 mt-4 items-center">
      {filterOptions.map((option, index)=>{
        return <ToggleGlowButton
        key={index}
        color="#34D399"
        active={filterIndex===index}
        onClick={()=>setFilterIndex(index)}
        >
          {option}
        </ToggleGlowButton>
      })}

      <p className="text-secondary-content ml-auto">
        {patrols.length} patrols
      </p>
    </div>

    <div className="mx-6 mt-5">
      {
        patrols.map((patrol, index)=>{
          return <PatrolCard
            key={index}
            color="#F97316"
            patrol={patrol}
            confirmIncident={()=>{}}
            dismissIncident={()=>{}}
            assignPatrol={()=>{}}
          />
      })
      }
  </div>
  </>
  );
}
