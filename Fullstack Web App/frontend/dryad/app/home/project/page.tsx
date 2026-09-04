"use client"

import { apiFetch } from "@/lib/api";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { FaArrowLeft } from "react-icons/fa";

import type { Member, Project } from "../projects/new/page";
import { IoIosStats, IoIosWarning, IoMdWifi } from "react-icons/io";
import { FaGear, FaMap } from "react-icons/fa6";
import { AiOutlineTeam } from "react-icons/ai";
import { useRouter } from "next/navigation";
import IncidentsView from "@/components/ProjectView/IncidentsView";
import type { ThreatClass } from "../projects/new/page";
import ForestMapView from "@/components/ProjectView/ForestMapView";
const { wktToGeoJSON } = require('@terraformer/wkt');

type Tab = "overview" | "incidents" | "forest_map" | "devices" | "team";

type Device = {
  id : number;
  name : string;
  location : string;
}

export type IncidentType = {
  id : number;
  coordinates : string;
  timestamp : string;
  confidence : number;
  status : string;
  project : number;
  threatClass : ThreatClass;
  device : Device;
}

export default function Project() {
  const searchParams = useSearchParams();
  const projectID = searchParams.get("pid");
  const tab = searchParams.get("tab");
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [incidents, setIncidents] = useState<IncidentType[]>([])
  const [filterIndex, setFilterIndex] = useState<number>(0);
  const [members, setMembers] = useState<Member[]>([]);
  const [threatClasses, setThreatClasses] = useState<ThreatClass[]>([]);
  const [gridCells, setGridCells] = useState(null);

  const extractProjectFeatures = (data : any) => {
    setProject({
      ...data.properties,
      area : data.properties.surface_area,
      id : data.id,
      geoJSON : data.monitoring_area
    })
  }

  const extractIncidents = (data : any)=>{
    setIncidents(data.map((incident : any)=>{
      return {...incident, threatClass : incident.threat_class}
    }))
  }

  const tabOptions = [
    {title : "Overview", href : "overview", icon : IoIosStats},
    {title : "Incidents", href : "incidents", icon : IoIosWarning },
    {title : "Forest Map", href : "forest_map", icon : FaMap },
    {title : "Devices", href : "devices", icon : IoMdWifi},
    {title : "Team", href : "team", icon : AiOutlineTeam},
    {title : "Settings", href : "settings", icon : FaGear},
  ]

  const filterOptions = [
    "All",
    "New",
    "High Priority",
    "Chainsaw",
    "Vehicles",
    "Tree Falling"
  ]

  const tabComponentMapping = {
    overview : <></>,
    incidents : <IncidentsView 
      projectID={projectID}
      filterIndex={filterIndex}
      filterOptions={filterOptions}
      setFilterIndex={(index)=>setFilterIndex(index)}
      incidents={incidents}
      threatClasses={threatClasses}
      setThreatClasses={setThreatClasses}
      setIncidents={setIncidents}
    />,
    forest_map : <ForestMapView
      projectID={projectID}
      geoJSON={project?.geoJSON}
      gridCells={gridCells}
    />,
    devices : <></>,
    team : <></>,
    settings : <></>,
  }

  const isValidTab = (tab: string | null): tab is Tab => {
    return tab !== null && tab in tabComponentMapping;
  };

  useEffect(()=>{
    // fetch project info
    apiFetch(`http://127.0.0.1:8000/api/projects/${projectID}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>extractProjectFeatures(data))
      .catch((err) => console.error("Fetch failed:", err));

    // fetch project incidents
    apiFetch(`http://127.0.0.1:8000/api/incidents?project=${projectID}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>extractIncidents(data))
      .catch((err) => console.error("Fetch failed:", err));

    // fetch project members
    apiFetch(`http://127.0.0.1:8000/api/members?project=${projectID}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>setMembers(data.map((member : any)=>{
        return {...member, 
          firstName : member.user.first_name, 
          lastName : member.user.last_name,
          email : member.user.email
        }
      })))
      .catch((err) => console.error("Fetch failed:", err));

    // fetch threat classes for incidents filter
    apiFetch(`http://127.0.0.1:8000/api/threat_classes/`)
    .then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    })
    .then((data)=>setThreatClasses(data))
    .catch((err) => console.error("Fetch failed:", err));

    // fetch project grid cells
    apiFetch(`http://127.0.0.1:8000/api/projects/${projectID}/grid_cells`)
    .then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    })
    .then((data)=>setGridCells(data))
    .catch((err) => console.error("Fetch failed:", err));
  }, [])

  return (<div className="flex flex-col">
      {project!=null ? 
      <>
        <div className="w-full bg-base-200 border-b border-b-white/8 pt-5 pb-3">
          <div className="flex flex-row items-center ml-6">
            <button onClick={()=>router.push("/home/projects")}
              className="btn btn-secondary font-medium">
              <FaArrowLeft/>
              Dashboard
            </button>
      
            <div className="ml-6 ">
              <h1 className="font-semibold text-xl">{project.name}</h1>
              <p className="text-secondary-content">{project.region} · {project.area}km²</p>
            </div>
          </div>

          <div className="ml-6 mt-4 flex flex-row">
            {tabOptions.map((tabOption, index)=>{
              const Icon = tabOption.icon;
              const active = tab===tabOption.href;
              return (
              <div 
              className={`${active ? 
                "text-accent bg-base-300 border-b border-b-2 border-b-accent" : 
                "text-secondary-content"} 
                rounded-t-2xl flex flex-row items-center py-2 px-4 cursor-pointer`}
              key={index}
              onClick={()=>router.push(`/home/project?pid=${projectID}&tab=${tabOption.href}`)}>
                <Icon className="mr-2 text-base"/>
                <h1>{tabOption.title}</h1>
              </div>)
            })}
          </div>
        </div>

        {isValidTab(tab) ? (
          tabComponentMapping[tab]
        ) : (
          <span className="loading loading-spinner"></span>
        )}  
      </>
      :

      <div className="w-full h-screen flex justify-center items-center">
        <span className="loading loading-spinner"></span>
      </div>}
    </div>);
}