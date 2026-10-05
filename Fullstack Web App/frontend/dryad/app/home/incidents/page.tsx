"use client"

import IncidentsView from "@/components/ProjectView/IncidentsView";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { IncidentType } from "../project/page";
import { ThreatClass } from "../projects/new/page";

export default function Incidents() {
  const searchParams = useSearchParams();
  const projectID = searchParams.get("pid");
  const router = useRouter();
  const [incidents, setIncidents] = useState<IncidentType[]>([])
  const [filterIndex, setFilterIndex] = useState<number>(0);
  const [threatClasses, setThreatClasses] = useState<ThreatClass[]>([]);

  const filterOptions = [
    "All",
    "New",
    "High Priority",
    "Chainsaw",
    "Vehicles",
    "Tree Falling"
  ]

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

    <IncidentsView 
      projectID={projectID}
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
