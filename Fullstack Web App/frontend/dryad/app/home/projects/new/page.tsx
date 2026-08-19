"use client"

import StepOnePage from "@/components/StepPages/StepOnePage";
import StepTwoPage from "@/components/StepPages/StepTwoPage";
import StepPanel from "@/components/StepPanel";
import Link from "next/link";
import { useState } from "react";
import { FaArrowLeft } from "react-icons/fa";
import type { GeoJSON } from 'geojson';
import StepThreePage from "@/components/StepPages/StepThreePage";
import StepFourPage from "@/components/StepPages/StepFourPage";
import StepFivePage from "@/components/StepPages/StepFivePage";
import L, { LatLng } from "leaflet";

export type Member = {
  id : number;
  firstName : string;
  lastName : string;
  email : string;
  role : string;
}

export type Project = {
  name : string;
  description : string;
  color : string;
  geoJSON : GeoJSON | null;
  area : number | null;
  members : Member[];
  region : string | null;
  center : LatLng | null;
}

export default function New() {
  const [step, setStep] = useState<number>(0);
  const [project, setProject] = useState<Project>({
    name : "",
    description : "",
    color : "#4ADE80",
    geoJSON : null,
    members : [],
    area : null,
    region : null,
    center : null
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
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${center?.lat}&lon=${center?.lng}&format=jsonv2`
    );
    const data = await response.json();
    setProject({...project, 
      area : area, geoJSON : 
      geoJSON, 
      region : `${data.address.state}, ${data.address.country}`,
      center : center
    })
  }

  const pages = [
    <StepOnePage 
      nameValue={project.name}
      nameFunction={(e)=>setProject({...project, name: e.target.value})}
      descriptionValue={project.description}
      descriptionFunction={(e)=>setProject({...project, description: e.target.value})}
      colorValue={project.color}
      colorFunction={(e)=>setProject({...project, color: e.target.value})}
      submitEvent={nextPage}/>,

    <StepTwoPage 
      backEvent={()=>setStep(step-1)}
      submitEvent={nextPage}
      handleArea={handleArea}
      forestArea={project.area}
      geoJSON={project.geoJSON}
      />,

    <StepThreePage 
      nameValue={project.name}
      nameFunction={(e)=>setProject({...project, name: e.target.value})}
      descriptionValue={project.description}
      descriptionFunction={(e)=>setProject({...project, description: e.target.value})}
      colorValue={project.color}
      colorFunction={(e)=>setProject({...project, color: e.target.value})}
      submitEvent={nextPage}
      backEvent={()=>setStep(step-1)}/>,

    <StepFourPage 
      membersArray={project.members}
      membersFunction={(newMemberArray : Member[])=>setProject({...project, members: newMemberArray})}
      roleFunction={changeRole}
      submitEvent={nextPage}
      backEvent={()=>setStep(step-1)}/>,

    <StepFivePage 
      project={project}
      submitEvent={nextPage}
      backEvent={()=>setStep(step-1)}/>,
  ]
  
  return (
  <div className="flex flex-col">
    <div className="fixed top-0 h-20 w-full flex flex-row items-center bg-secondary border-b border-b-white/8 z-1">
      <button onClick={()=>console.log(project)}
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
