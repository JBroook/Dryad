"use client"

import { FaCircle } from "react-icons/fa";
import CurrentStep from "./Steps/CurrentStep";
import CompletedStep from "./Steps/CompletedStep";
import NextStep from "./Steps/NextStep";
import { FaRegClipboard } from "react-icons/fa6";
import { CiGlobe } from "react-icons/ci";
import { IoMdCheckmark, IoMdWifi } from "react-icons/io";
import { AiOutlineTeam } from "react-icons/ai";

interface StepPanelProps {
    currentStep : number;
}

export default function StepPanel(props: StepPanelProps) {
    const steps = [
        {title : "Basics", icon : FaRegClipboard},
        {title : "Location", icon : CiGlobe},
        {title : "Detection", icon : IoMdWifi},
        {title : "Team", icon : AiOutlineTeam},
        {title : "Review", icon : IoMdCheckmark},
    ]

    return (<aside className="w-64 shrink-0 ">
        <div className="fixed 
        top-16 w-64 bg-secondary h-screen border-l 
        border-l-white/8 border-l-width-[2px]
        flex flex-col items-center px-5 pt-10
        ">
            {steps.map((step, index)=>{
                if(props.currentStep==index){
                    return <CurrentStep title={step.title} icon={step.icon} step={index} key={index}/>
                }else if(props.currentStep>index){
                    return <CompletedStep title={step.title} icon={step.icon} step={index} key={index}/>
                }else{
                    return <NextStep title={step.title} icon={step.icon} step={index} key={index}/>
                }
            })}
        </div>
    </aside>);
}