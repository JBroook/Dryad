"use client"

import HollowCard from "@/components/HollowCard";
import ProjectCard from "@/components/ProjectCard";
import ProjectCreator from "@/components/ProjectCreator";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { BsTree } from "react-icons/bs";
import { FaPlus } from "react-icons/fa6";
import { GoPulse } from "react-icons/go";
import { IoMdWifi } from "react-icons/io";
import { IoWarning } from "react-icons/io5";

import type { Project } from "./new/page";

export default function Home() {
  const [authenticated, setAuthenticated] = useState<boolean>(false)
  const [projectsLoaded, setProjectsLoaded] = useState<boolean>(false)
  const router = useRouter();
  const overviewCards = [
    {title : "Active Projects", number : 2, icon : BsTree, iconColor : "#4ADE80"},
    {title : "New Incidents", number : 2, icon : IoWarning, iconColor : "#F87171"},
    {title : "Online Devices", number : 5, icon : IoMdWifi, iconColor : "#60A5FA"},
    {title : "Total Incidents", number : 8, icon : GoPulse, iconColor : "#A78BFA"},
  ]

  const [firstName, setFirstName] = useState<string>("")
  const [allProjects, setAllProjects] = useState<Project[]>([])

  useEffect(()=>{
    const token = localStorage.getItem("access");

    if(!token){
      router.push("/login")
    }else{
      setAuthenticated(true)
    }

    // fetch user info
    const userID = localStorage.getItem("userID")
    apiFetch(`http://127.0.0.1:8000/api/users/${userID}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>{
        setFirstName(data.first_name)
        return data
      })
      .catch((err) => console.error("Fetch failed:", err));

    const extractProjectFeatures = (data : any) => {
      const extractedProjects = data.features.map((feature : any)=>{
        return {
          ...feature.properties, 
          area : feature.properties.surface_area,
          id : feature.id
        }
      })
      setAllProjects(extractedProjects)
      setProjectsLoaded(true);
    }

    // fetch all projects
    apiFetch(`http://127.0.0.1:8000/api/projects/`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then(extractProjectFeatures)
      .catch((err) => console.error("Fetch failed:", err));
  }, [])

  return (<>
    {authenticated ?
      <>

        <div className="w-full py-5 pl-8 border-b-white/8 border-b border-b-width-[2px] flex flex-row items-center justify-between ">
          <div>
            <h1 className="font-bold text-2xl">
              Projects
            </h1>
            <p className="text-sm text-secondary-content">
              Welcome back, {firstName}
            </p>
          </div>

          <Link 
              href="/home/projects/new"
              className="btn btn-primary mr-8"
          >
              <FaPlus/>
              New Project
          </Link>
        </div>

        <div className="w-full grid grid-cols-4 gap-4 px-8 mt-8">
            {overviewCards.map((card, index)=>{
              const Icon = card.icon;
              return (<HollowCard key={index}>
                  <div className="stat">
                    <div className="stat-figure text-primary">
                      <Icon className="text-2xl" style={{color : card.iconColor}}/>
                    </div>
                    <div className="stat-title">{card.title}</div>
                    <div className="stat-value mt-2">{card.number}</div>
                  </div>
                </HollowCard>);
            })}
        </div>

        <h2 className="ml-8 mt-8 mb-4 font-semibold">
          Your Projects
        </h2>
        {  !projectsLoaded ? 
          <div className="w-full h-fit py-25 flex justify-center items-center">
            <span className="loading loading-spinner"></span>
          </div>
        :
          <div className="grid w-full max-w-full grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-x-3 gap-y-5 px-8 mb-32">

            {allProjects.map((project, index)=>{
              return <ProjectCard
                key={index}
                tag ={project.status ? "Active" : "Inactive"}
                name ={project.name}
                region ={project.region!}
                area ={project.area!}
                alerts ={1}
                activeDevices ={3}
                totalDevices ={5}
                members ={20}
                accentColor={project.color}
                tagColor="#4ADE80"
                openProject={()=>{router.push(`/home/project?pid=${project.id}&tab=overview`)}}
              />
            })}

            <Link className="flex flex-col justify-center 
            items-center rounded-xl border border-white/8
            cursor-pointer hover:bg-base-300 min-h-50 bg-base-200 max-w-[400px]"
            href="/home/projects/new"
            >
                <div className="rounded-full border border-primary bg-base-300 p-2 mb-2">
                  <FaPlus className="text-accent"/>
                </div>
              <p className="text-secondary-content text-sm">Add new project</p>
            </Link>
          </div>
          }
      </>
      :
      <div className="w-full h-screen flex justify-center items-center">
        <span className="loading loading-spinner"></span>
      </div>
    }
  </>
  );
}
