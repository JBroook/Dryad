"use client"

import { apiFetch } from "@/lib/api";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { FaArrowLeft } from "react-icons/fa";

import type { Project } from "../projects/new/page";
import { IoIosStats, IoIosWarning, IoMdWifi } from "react-icons/io";
import { FaMap } from "react-icons/fa6";
import { AiOutlineTeam } from "react-icons/ai";
import { useRouter } from "next/navigation";
import IncidentsView from "@/components/ProjectView/IncidentsView";

type Tab = "overview" | "incidents" | "forest_map" | "devices" | "team";

export default function Project() {
  const searchParams = useSearchParams();
  const projectID = searchParams.get("pid");
  const tab = searchParams.get("tab");
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [filterIndex, setFilterIndex] = useState<number>(0);

  const extractProjectFeatures = (data : any) => {
    setProject({
      ...data.properties,
      area : data.properties.surface_area,
      id : data.id
    })
  }

  const tabOptions = [
    {title : "Overview", href : "overview", icon : IoIosStats},
    {title : "Incidents", href : "incidents", icon : IoIosWarning },
    {title : "Forest Map", href : "forest_map", icon : FaMap },
    {title : "Devices", href : "devices", icon : IoMdWifi},
    {title : "Team", href : "team", icon : AiOutlineTeam},
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
      filterIndex={filterIndex}
      filterOptions={filterOptions}
      setFilterIndex={(index)=>setFilterIndex(index)}
    />,
    forest_map : <></>,
    devices : <></>,
    team : <></>,
  }

  const isValidTab = (tab: string | null): tab is Tab => {
    return tab !== null && tab in tabComponentMapping;
  };

  useEffect(()=>{
    // fetch all projects
    apiFetch(`http://127.0.0.1:8000/api/projects/${projectID}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>extractProjectFeatures(data))
      .catch((err) => console.error("Fetch failed:", err));
  }, [])

  return (<div className="flex flex-col">
      {project!=null ? 
      <>
        <div className="w-full bg-base-200 border-b border-b-white/8 pt-5 pb-3">
          <div className="flex flex-row items-center ml-6">
            <button onClick={()=> window.history.back()}
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
