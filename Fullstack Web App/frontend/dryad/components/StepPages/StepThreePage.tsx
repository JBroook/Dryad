import Link from "next/link";
import { FaArrowLeft, FaArrowRight, FaMicrophone, FaTree, FaTruck } from "react-icons/fa";
import BottomBar from "./BottomBar";
import { useState } from "react";
import { GiChainsaw } from "react-icons/gi";
import { IoMdCheckmark } from "react-icons/io";
import ThreatClassOption from "../ThreatClassOption";
import { TbEngineFilled } from "react-icons/tb";

interface StepPageProps {
    submitEvent : () => void;
    backEvent : () => void;
}

type ThreatClass = {
    name : string;
    description : string;
    active : boolean;
}

export default function StepThreePage(props: StepPageProps) {
    const [threatClasses, setThreatClasses] = useState<ThreatClass[]>([
        {name : "Chainsaw", description : "High-frequency acoustic signature of chainsaws", active : true},
        {name : "Vehicle", description : "Heavy diesel engine noise patterns", active : true},
        {name : "Treefall", description : "Impact and cracking sounds of falling trees", active : true},
        {name : "Generator", description : "Rumbling sounds of generators used to power logging sites", active : true},
    ]);

    const associatedIcon : any = {
        Chainsaw : FaMicrophone,
        Vehicle : FaTruck,
        Treefall : FaTree,
        Generator : TbEngineFilled
    }

    const switchActive = (index : number) => {
        console.log(index)
        const newThreatClasses = [
            ...threatClasses
        ]
        newThreatClasses[index].active = !newThreatClasses[index].active
        setThreatClasses(newThreatClasses);
    }

    return (
    <div className="h-[calc(100vh-5rem)] flex flex-col">
        <div className="flex flex-row ml-30 mt-8">
          <p className="text-sm text-secondary-content">Step 3 of 5</p>
          <p className="text-sm text-accent ml-5 font-semibold">Detection</p>
        </div>

        <h1 className="pt-3 text-3xl font-bold mx-30">Configure Detection Devices</h1>
        <p className="pt-2 text-secondary-content mx-30">Set up the acoustic detection parameters for your sensor network.</p>

        <form className="pt-6 flex-1" onSubmit={props.submitEvent} id="project-form">
            <div className="mx-30">
                <div className="flex flex-row w-full">
                    <fieldset className="fieldset pt-2 flex-1 mr-2">
                        <legend className="fieldset-legend font-medium text-secondary-content">Confidence Threshold (%)</legend>
                        
                        <input
                        type="number"
                        className="input w-full bg-base-200 border"
                        placeholder="e.g. 75"
                        // value={props.nameValue}
                        // onChange={props.nameFunction}
                        />
                    </fieldset>

                    <fieldset className="fieldset pt-2 flex-1 ml-2">
                        <legend className="fieldset-legend font-medium text-secondary-content">Alert Preference</legend>
                        
                        <select defaultValue="All" className="select w-full bg-base-200 border">
                            <option>All</option>
                            <option>Managers and above</option>
                            <option>Admins and above</option>
                            <option>Owner only</option>
                        </select>
                    </fieldset>
                </div>

                <fieldset className="fieldset pt-2">
                    <legend className="fieldset-legend font-medium text-secondary-content">Threat Classes</legend>

                    <div className="w-full mb-20">
                        {threatClasses.map((threatClass, index)=>{
                            return <ThreatClassOption 
                                key={index}
                                setActive={()=>switchActive(index)}
                                name={threatClass.name}
                                description={threatClass.description}
                                active={threatClass.active}
                                icon={associatedIcon[threatClass.name]}
                            />
                        })}

                        <p className="text-secondary-content text-sm"><i>Select the types of audio that you want Dryad to look out for</i></p>
                    </div>
                </fieldset>

                {/* <fieldset className="fieldset pt-2">
                    <legend className="fieldset-legend font-medium text-secondary-content">Threat Classes</legend>
                    
                    <textarea
                    className="textarea w-full bg-base-200 border resize-none"
                    placeholder="Briefly describe what this project is protecting and why it matters"
                    // value={props.descriptionValue}
                    // onChange={props.descriptionFunction}
                    />
                </fieldset> */}
            </div>
        </form>

        <BottomBar ready={true} next="Continue" back="Back" formID="project-form" backEvent={props.backEvent}/>
    </div>);
}