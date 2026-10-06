"use client"

import { useEffect, useState } from "react";
import { IncidentType } from "../project/page";
import { ThreatClass } from "../projects/new/page";
import FullIncidentsView from "@/components/FullIncidentsView";
import { apiFetch } from "@/lib/api";

export default function Incidents() {
  const [incidents, setIncidents] = useState<IncidentType[]>([])
  const [filterIndex, setFilterIndex] = useState<number>(0);
  const [threatClasses, setThreatClasses] = useState<ThreatClass[]>([]);
  const [userID, setUserID] = useState<string | null>(null);

  const filterOptions = [
    "All",
    "New",
    "High Priority",
    "Chainsaw",
    "Vehicles",
    "Tree Falling"
  ]

  const extractIncidents = (data : any)=>{
    setIncidents(data.map((incident : any)=>{
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
    const tempUserID = localStorage.getItem("userID")
    setUserID(tempUserID)
    // fetch all user's incidents
    apiFetch(`http://127.0.0.1:8000/api/incidents?user_id=${tempUserID}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>{console.log(data); return data})
      .then((data)=>extractIncidents(data))
      .catch((err) => console.error("Fetch failed:", err));
  }, [])

  return (<>
    <div className="w-full py-5 pl-8 border-b-white/8 border-b border-b-width-[2px] flex flex-row items-center justify-between ">
      <div>
        <h1 className="font-bold text-2xl">
          Incidents
        </h1>
        <p className="text-sm text-secondary-content">
          View all incidents detected by listening devices
        </p>
      </div>
    </div>

    <FullIncidentsView 
      userID={userID}
      filterIndex={filterIndex}
      filterOptions={filterOptions}
      setFilterIndex={(index)=>setFilterIndex(index)}
      incidents={incidents}
      threatClasses={threatClasses}
      setThreatClasses={setThreatClasses}
      setIncidents={setIncidents}
    />
  </>
  );
}
