import { FaRegClipboard } from "react-icons/fa";
import BottomBar from "./BottomBar";
import { IoIosInformationCircleOutline, IoMdWifi } from "react-icons/io";
import InfoTable from "../InfoTable";
import { CiGlobe } from "react-icons/ci";
import { AiOutlineTeam } from "react-icons/ai";
import { Project } from "@/app/home/projects/new/page";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface StepPageProps {
    submitEvent : () => Promise<number | null>;
    backEvent : () => void;
    project : Project;
}

export default function StepFivePage(props: StepPageProps) {
    const router = useRouter();
    const [creationComplete, setCreationComplete] = useState<boolean>(false);
    const [projectId, setProjectId] = useState<number | null>(null);

    const basics = [
        {key : "Name", value : props.project.name},
        {key : "Description", value : props.project.description!="" ? props.project.description : "-"},
        {key : "Color", value : props.project.color},
    ]

    const centerAsString = `${props.project.center?.lat?.toString()}°, ${props.project.center?.lng?.toString()}°`;
    const location = [
        {key : "Region", value : props.project.region ? props.project.region : "Undefined"},
        {key : "Coordinates", value : centerAsString},
        {key : "Monitored Area", value : props.project.area ? props.project.area.toString()+"km²" : "0km²"},
    ]

    const threatClasses = props.project.threatClasses
    .filter((threatClass)=>threatClass.active)
    .map((threatClass)=>threatClass.name)
    const detection = [
        {key : "Threat Classes", value : threatClasses.join(", ")},
        {key : "Confidence Threshold", value : `${props.project.confidenceThreshold}%`},
        {key : "Alert Recipients", value : props.project.alertPreference},
    ]

    const team = [
        {key : "Owner", value : "You"},
        {key : "Members", value : (props.project.members.length+1).toString()}
    ]

    const openModal = ()=>{
        const modal = document.getElementById('submitModal') as HTMLDialogElement;
        modal.showModal();
    }

    const submitEvent = async ()=>{
        openModal();
        const createdProjectId = await props.submitEvent();

        if (createdProjectId) {
            setProjectId(createdProjectId);
            setCreationComplete(true);
        }
    }

    return (<>
    <dialog id="submitModal" className="modal">
        <div className="modal-box bg-base-200 border border-white/8 flex flex-col items-center">
                {!creationComplete ?
                <>
                    <h3 className="font-bold text-lg">Project Creation in Progress...</h3>
                    <p className="py-4 text-sm text-secondary-content">
                    Please wait while your project is created. This process may take a few minutes.
                    </p>
                    <span className="loading loading-spinner"></span>
                </>
                :
                <>
                    <h3 className="font-bold text-lg">Project Created!</h3>
                    <p className="pt-4 text-sm text-secondary-content">
                    Your project, {props.project.name}, is ready!
                    </p>
                    <div className="modal-action justify-end">
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={() => {
                                if (projectId !== null) {
                                    router.push(`/project?pid=${projectId}`);
                                }
                            }}
                        >
                            Open Project
                        </button>
                    </div>
                </>
                }
        </div>
    </dialog>

    <div className="h-[calc(100vh-5rem)] flex flex-col">
        <div className="flex flex-row ml-30 mt-8">
          <p className="text-sm text-secondary-content">Step 5 of 5</p>
          <p className="text-sm text-accent ml-5 font-semibold">Review</p>
        </div>

        <h1 className="pt-3 text-3xl font-bold mx-30">Review & Create</h1>
        <p className="pt-2 text-secondary-content mx-30">Does everything look good? Create your project and start protecting.</p>

        <div className="mx-30 flex-1 mb-20">
            <div className="bg-info/8 rounded-xl border border-info/50 mt-8 flex flex-row px-4 py-5 mb-5">
                <IoIosInformationCircleOutline className="text-info text-xl mr-4"/>
                <p className="text-info text-sm">Review your project configuration below. You can go back and edit any step before creating.</p>
            </div>

            <InfoTable 
                title="Project Basics"
                icon={FaRegClipboard}
                keyValuePairs={basics}
            />

            <InfoTable 
                title="Location"
                icon={CiGlobe}
                keyValuePairs={location}
            />

            <InfoTable 
                title="Detection"
                icon={IoMdWifi}
                keyValuePairs={detection}
            />

            <InfoTable 
                title="Team"
                icon={AiOutlineTeam}
                keyValuePairs={team}
            />
        </div>

        <BottomBar ready={true} next="Create Project" back="Back" formID="project-form" backEvent={props.backEvent} nextEvent={submitEvent}/>
    </div>
    </>);
}