import { FaArrowLeft, FaArrowRight, FaRegClipboard } from "react-icons/fa";
import BottomBar from "./BottomBar";
import { IoIosInformationCircleOutline, IoMdWifi } from "react-icons/io";
import InfoTable from "../InfoTable";
import { CiGlobe } from "react-icons/ci";
import { AiOutlineTeam } from "react-icons/ai";
import { Project } from "@/app/home/projects/new/page";

interface StepPageProps {
    submitEvent : () => void;
    backEvent : () => void;
    project : Project;
}

export default function StepFivePage(props: StepPageProps) {
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

    const detection = [
        {key : "Devices", value : "10"},
        {key : "Threat Classes", value : "Chainsaw, Vehicles, Treefall, Generator"},
        {key : "Confidence Threshold", value : "75%"},
        {key : "Alert Recipients", value : "All"},
    ]

    const team = [
        {key : "Owner", value : "You"},
        {key : "Members", value : props.project.members.length.toString()}
    ]
    return (
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

        <BottomBar ready={true} next="Create Project" back="Back" formID="project-form" backEvent={props.backEvent}/>
    </div>);
}