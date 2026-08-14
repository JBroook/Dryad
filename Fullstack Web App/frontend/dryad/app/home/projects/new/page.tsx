  "use client"

import StepOnePage from "@/components/StepPages/StepOnePage";
import StepTwoPage from "@/components/StepPages/StepTwoPage";
import StepPanel from "@/components/StepPanel";
import Link from "next/link";
import { useState } from "react";
import { FaArrowLeft } from "react-icons/fa";

export default function New() {
  const [step, setStep] = useState<number>(0);
  const [projectName, setProjectName] = useState<string>("");
  const [projectDescription, setProjectDescription] = useState<string>("");
  const [projectColor, setProjectColor] = useState<string>("#4ADE80");

  const nextPage = () => {
    setStep(step+1);
  }

  const pages = [
    (<StepOnePage 
      nameValue={projectName}
      nameFunction={(e)=>setProjectName(e.target.value)}
      descriptionValue={projectDescription}
      descriptionFunction={(e)=>setProjectDescription(e.target.value)}
      colorValue={projectColor}
      colorFunction={(e)=>setProjectColor(e.target.value)}
      submitEvent={nextPage}/>),

      (<StepTwoPage backEvent={()=>setStep(step-1)}/>),
  ]
  
  return (
  <div className="flex flex-col">
    <div className="fixed top-0 h-20 w-full flex flex-row items-center bg-secondary border-b border-b-white/8 z-1">
      <Link href="/home/projects" 
        className="btn text-secondary-content font-medium ml-5">
        <FaArrowLeft className="text-secondary-content"/>
        Dashboard
      </Link>

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
