"use client"

import StepOnePage from "@/components/StepPages/StepOnePage";
import StepTwoPage from "@/components/StepPages/StepTwoPage";
import StepPanel from "@/components/StepPanel";
import { useEffect, useState } from "react";
import { FaArrowLeft } from "react-icons/fa";
import type { GeoJSON } from 'geojson';
import StepThreePage from "@/components/StepPages/StepThreePage";
import StepFourPage from "@/components/StepPages/StepFourPage";
import StepFivePage from "@/components/StepPages/StepFivePage";
import { LatLng } from "leaflet";
import { apiFetch } from "@/lib/api";

export type Member = {
  id : number;
  firstName : string;
  lastName : string;
  email : string;
  role : string;
  joinDate : string;
  accepted? : boolean;
  user?: {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
  };
}

export type ThreatClass = {
  id : number;
  name : string;
  description : string;
  active : boolean;
}

export type Project = {
  id : number;
  name : string;
  description : string;
  color : string;
  geoJSON : GeoJSON | null;
  area : number | null;
  members : Member[];
  region : string | null;
  center : LatLng | null;
  confidenceThreshold : number;
  threatClasses : ThreatClass[];
  alertPreference : string;
  status : boolean;
  memberCount? : number;
  deviceCount? : number;
  newAlerts? : number;
  trainCount : number;
  lastTrained : string | null;
}

export default function New() {
  const [step, setStep] = useState<number>(0);
  const [project, setProject] = useState<Project>({
    id : -1,
    name : "",
    status : true,
    description : "",
    color : "#4ADE80",
    geoJSON : null,
    members : [],
    area : null,
    region : null,
    center : null,
    confidenceThreshold : 75,
    threatClasses : [],
    alertPreference : "all",
    trainCount : 0,
    lastTrained : null
  });

  const nextPage = () => {
    setStep(step+1);
  }

  const changeRole = (index : number, newRole : string) => {
    setProject({
      ...project,
      members: project.members.map((member, i) => 
        i === index ? { ...member, role: newRole } : member
      )
    });
  }

  const handleArea = async (geoJSON : GeoJSON | null, area : number | null, center : LatLng | null)=>{
    let newRegion = null;
    if(geoJSON){
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${center?.lat}&lon=${center?.lng}&format=jsonv2`
      );
      const data = await response.json();
      newRegion = `${data.address.state}, ${data.address.country}`
    }
    setProject({...project, 
      area : area, 
      geoJSON : geoJSON, 
      region : newRegion,
      center : center
    })
  }

  const createProject = async (): Promise<number | null> => {
    console.log(project)

    const monitoringArea =
      project.geoJSON && "geometry" in project.geoJSON
        ? project.geoJSON.geometry
        : project.geoJSON;

    try {
      const res = await apiFetch(`http://127.0.0.1:8000/api/projects/`, {
        method : "POST",
        headers : {
          "Content-Type" : "application/json",
        },
        body : JSON.stringify({
          ...project,
          coordinates : `${project.center!.lat},${project.center!.lng}`,
          surface_area : project.area,
          confidence_threshold : project.confidenceThreshold,
          alert_recipients : project.alertPreference,
          threat_classes : project.threatClasses.filter((threatClass)=>threatClass.active),
          monitoring_area : monitoringArea
        })
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText);
      }

      const data = await res.json();
      return Number(data.id);
    } catch (err) {
      console.error("Fetch failed:", err);
      return null;
    }
  }

  const setThreatClasses = (index : number) => {
    const newProject = {...project};
    newProject.threatClasses[index].active = !newProject.threatClasses[index].active;
    setProject(newProject);
  }

  const pages = [
    <StepOnePage
      key="step-one"
      nameValue={project.name}
      nameFunction={(e)=>setProject({...project, name: e.target.value})}
      descriptionValue={project.description}
      descriptionFunction={(e)=>setProject({...project, description: e.target.value})}
      colorValue={project.color}
      colorFunction={(e)=>setProject({...project, color: e.target.value})}
      submitEvent={nextPage}/>,

    <StepTwoPage
      key="step-two"
      backEvent={()=>setStep(step-1)}
      submitEvent={nextPage}
      handleArea={handleArea}
      forestArea={project.area}
      geoJSON={project.geoJSON}
      />,

    <StepThreePage
      key="step-three"
      submitEvent={nextPage}
      backEvent={()=>setStep(step-1)}
      confidenceThreshold={project.confidenceThreshold}
      setConfidenceThreshold={(e)=>setProject({...project, confidenceThreshold: parseInt(e.target.value)})}
      alertPreference={project.alertPreference}
      setAlertPreference={(e)=>setProject({...project, alertPreference: e.target.value})}
      threatClasses={project.threatClasses}
      setThreatClasses={setThreatClasses}
      />,

    <StepFourPage
      key="step-four"
      membersArray={project.members}
      membersFunction={(newMemberArray : Member[])=>setProject({...project, members: newMemberArray})}
      roleFunction={changeRole}
      submitEvent={nextPage}
      backEvent={()=>setStep(step-1)}/>,

    <StepFivePage
      key="step-five"
      project={project}
      submitEvent={createProject}
      backEvent={()=>setStep(step-1)}/>,
  ]

  useEffect(()=>{
    apiFetch(`http://127.0.0.1:8000/api/threat_classes/`)
    .then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    })
    .then((data)=>{
      data = data.map((threatClass : ThreatClass)=>{
        return {...threatClass, active : true}
      })
      setProject((currentProject) => ({ ...currentProject, threatClasses : data }))
    })
    .catch((err) => console.error("Fetch failed:", err));
  }, [])
  
  return (
  <div className="flex flex-col">
    <div className="fixed top-0 h-20 w-full flex flex-row items-center bg-base-200 border-b border-b-white/8 z-1">
      <button onClick={()=> window.history.back()}
        className="btn text-secondary-content font-medium ml-5">
        <FaArrowLeft className="text-secondary-content"/>
        Dashboard
      </button>

      <h1 className="ml-10">New Monitoring Project</h1>
    </div>

    <div className="flex mt-20">
      <div className="flex-1 min-w-0">
        {pages[step]}
      </div>

      <StepPanel currentStep={step} />
    </div>
  </div>
  );
}
