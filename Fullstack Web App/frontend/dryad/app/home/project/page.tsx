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

export default function Project() {
  const searchParams = useSearchParams();
  const projectID = searchParams.get("pid");
  const tab = searchParams.get("tab");
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);

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
      <div className="fixed top-0 w-full bg-secondary border-b border-b-white/8 z-1 py-5">
        <div className="flex flex-row items-center ml-6">
          <button onClick={()=> window.history.back()}
            className="btn text-secondary-content font-medium">
            <FaArrowLeft className="text-secondary-content"/>
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
              rounded-t-2xl flex flex-row items-center text-base mr-4 py-2 px-4 cursor-pointer`}
            key={index}
            onClick={()=>router.push(`/home/project?pid=${projectID}&tab=${tabOption.href}`)}>
              <Icon className="mr-2"/>
              <h1>{tabOption.title}</h1>
            </div>)
          })}
        </div>
      </div>

      :

      <div className="w-full h-screen flex justify-center items-center">
        <span className="loading loading-spinner"></span>
      </div>}
    </div>);
}
