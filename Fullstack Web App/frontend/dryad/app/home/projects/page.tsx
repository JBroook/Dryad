"use client"

import HollowCard from "@/components/HollowCard";
import ProjectCard from "@/components/ProjectCard";
import ProjectCreator from "@/components/ProjectCreator";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { IconType } from "react-icons";
import { BsTree } from "react-icons/bs";
import { FaCheck, FaPlus, FaRegBell, FaUserPlus } from "react-icons/fa6";
import { GoPulse } from "react-icons/go";
import { IoMdWifi } from "react-icons/io";
import { IoWarning } from "react-icons/io5";

import type { Project } from "./new/page";
import { timeAgo } from "@/lib/general";
import { RxCross2 } from "react-icons/rx";

interface OverviewCard {
  title: string;
  number: number | null;
  icon: IconType;
  iconColor: string;
}

export default function Home() {
  const [authenticated, setAuthenticated] = useState<boolean>(false)
  const [projectsLoaded, setProjectsLoaded] = useState<boolean>(false)
  const router = useRouter();
  const [firstName, setFirstName] = useState<string>("")
  const [allProjects, setAllProjects] = useState<Project[]>([])
  const [notifications, setNotifications] = useState<any[]>([])
  const [overviewCards, setOverviewCards] = useState<OverviewCard[]>([
    {title : "Active Projects", number : null, icon : BsTree, iconColor : "#4ADE80"},
    {title : "New Incidents", number : null, icon : IoWarning, iconColor : "#F87171"},
    {title : "Online Devices", number : null, icon : IoMdWifi, iconColor : "#60A5FA"},
    {title : "Total Incidents", number : null, icon : GoPulse, iconColor : "#A78BFA"},
  ])

  const extractPendingInvites = (data: any[]) => {
    const newNotifications = data.filter((member: any) => member.accepted === false)
    setNotifications(newNotifications)
  }

  const extractProjectFeatures = (data : any) => {
    const extractedProjects = data.map((project : any)=>{
      return {
        ...project, 
        area : project.surface_area,
        memberCount : project.member_count,
        deviceCount : project.device_count,
        newAlerts : project.new_alerts
      }
    })
    setAllProjects(extractedProjects)
    setProjectsLoaded(true);
  }

  const acceptInvitation = (notificationIndex : number, accept : boolean) => {
    apiFetch(`http://127.0.0.1:8000/api/memberships/${notifications[notificationIndex].id}/accept_invite`, {
      method : "POST",
      body : JSON.stringify({
        accepted : accept
      })
    })
    .then(async (res) => {
    if (!res.ok) throw new Error(await res.text());
    })
    .then(()=>{
      const newNotifications = [...notifications]
      newNotifications.splice(notificationIndex, 1)
      setNotifications(newNotifications)
    })
    .catch((err) => console.error("Fetch failed:", err));
  }

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

    // fetch all projects
    apiFetch(`http://127.0.0.1:8000/api/projects/overview`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>{console.log(data); return data})
      .then(extractProjectFeatures)
      .catch((err) => console.error("Fetch failed:", err));

    // fetch overview info
    apiFetch(`http://127.0.0.1:8000/api/users/${userID}/overview`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>{
        const newOverviewCards = [...overviewCards]
        newOverviewCards[0].number = data.active_projects
        newOverviewCards[1].number = data.new_incidents
        newOverviewCards[2].number = data.online_devices
        newOverviewCards[3].number = data.total_incidents
        setOverviewCards(newOverviewCards)
      })
      .catch((err) => console.error("Fetch failed:", err));

    // fetch invites
    apiFetch(`http://127.0.0.1:8000/api/users/${userID}/memberships`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then(extractPendingInvites)
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

          <div className="flex items-center gap-2">
            <details className="dropdown dropdown-end dropdown-bottom">
              <summary className="btn btn-ghost btn-circle list-none">
                <div className="indicator">
                  {notifications.length > 0 && (
                    <span className="indicator-item badge badge-error badge-xs px-1">
                      {notifications.length}
                    </span>
                  )}

                  <FaRegBell className="text-xl text-accent"/>
                </div>
              </summary>

              <div className="menu dropdown-content bg-secondary rounded-box z-1 w-52 p-4 w-100 max-h-100 flex flex-col divide-y divide-base-300">
                <h1 className="font-semibold">Notifications ({notifications.length})</h1>

                {notifications.map((invite, index)=>{
                  const invitationDate = timeAgo(invite?.invited_on ?? Date.now())
                  const inviterName = invite?.invited_by ? `${invite.invited_by.first_name ?? ""} ${invite.invited_by.last_name ?? ""}`.trim() : "Someone"
                  const projectName = invite?.project?.name ?? "a project"
                  const roleText = invite?.role ?? "member"

                  return (<div className="flex mt-2" key={invite.id}>
                    <FaUserPlus className="text-primary text-xl m-2"/>
                    <div className="ml-2">
                      <p>
                        <strong>{inviterName}</strong> invited you to {projectName} as {roleText}
                      </p>
                      <p className="text-sm text-secondary-content">{invitationDate}</p>

                      <div className="flex gap-4 mt-2">
                        <button className="btn btn-sm btn-error"
                        onClick={()=>acceptInvitation(index, false)}>
                          <RxCross2/> Decline
                        </button>
                        <button className="btn btn-sm btn-accent"
                        onClick={()=>acceptInvitation(index, true)}>
                          <FaCheck /> Accept
                        </button>
                      </div>
                    </div>
                  </div>)
                })}
              </div>
            </details>

            <Link 
                href="/home/projects/new"
                className="btn btn-primary mr-8">
                <FaPlus/>
                New Project
            </Link>
          </div>
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
                {card.number!==null ?
                  <div className="stat-value mt-2">{card.number}</div>
                  :
                  <span className="loading loading-spinner"></span>
                }
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
                alerts ={project.newAlerts ?? 0}
                totalDevices ={project.deviceCount!}
                members ={project.memberCount!}
                accentColor={project.color}
                tagColor="#4ADE80"
                openProject={()=>{router.push(`/home/project?pid=${project.id}&tab=forest_map`)}}
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
