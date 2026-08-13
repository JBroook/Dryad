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
    const progress = Math.round(props.currentStep/steps.length*100);

    return (<aside className="w-64 shrink-0 ">
        <div className="fixed 
        top-16 w-64 bg-secondary bottom-0 border-l 
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

            <div className="flex-1 w-full relative">
                <div className="w-full flex flex-row justify-between absolute bottom-16">
                    <p className="text-secondary-content">Progress</p>
                    <p className="text-secondary-content">{progress}%</p>
                </div>
                <progress className="progress progress-primary w-56 absolute bottom-12" value={progress} max="100"></progress>
            </div>
        </div>
    </aside>);
}