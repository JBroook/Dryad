import Link from "next/link";
import { FaArrowLeft, FaArrowRight } from "react-icons/fa";
import BottomBar from "./BottomBar";

interface StepPageProps {
    backEvent : ()=>void;
    // submitEvent : () => void;
    // nameValue : string;
    // descriptionValue : string;
    // colorValue : string;
    // nameFunction : (e : React.ChangeEvent<HTMLInputElement>) => void;
    // descriptionFunction : (e : React.ChangeEvent<HTMLTextAreaElement>) => void;
    // colorFunction : (e : React.ChangeEvent<HTMLInputElement>) => void;
}

export default function StepOnePage(props: StepPageProps) {
    return (
    <div className="h-[calc(100vh-5rem)] flex flex-col">
        {/* <div className="flex flex-row ml-30 mt-8">
          <p className="text-sm text-secondary-content">Step 1 of 5</p>
          <p className="text-sm text-accent ml-5 font-semibold">Basics</p>
        </div>

        <h1 className="pt-3 text-3xl font-bold mx-30">Project Basics</h1>
        <p className="pt-2 text-secondary-content mx-30">Name your project and define what you're protecting.</p>

        <form className="pt-6 flex-1" onSubmit={props.submitEvent} id="project-form">
            <div className="mx-30">
                <fieldset className="fieldset">
                    <legend className="fieldset-legend font-medium text-secondary-content">Project Name</legend>
                    <input
                    type="text"
                    className="input w-full bg-base-200 border"
                    placeholder="e.g. Amazon Shield"
                    value={props.nameValue}
                    onChange={props.nameFunction}
                    />
                </fieldset>

                <fieldset className="fieldset pt-2">
                    <legend className="fieldset-legend font-medium text-secondary-content">Description</legend>
                    <textarea
                    className="textarea w-full bg-base-200 border resize-none"
                    placeholder="Briefly describe what this project is protecting and why it matters"
                    value={props.descriptionValue}
                    onChange={props.descriptionFunction}
                    />
                </fieldset>

                <fieldset className="fieldset pt-2">
                    <legend className="fieldset-legend font-medium text-secondary-content">Pick a Color</legend>
                    <input type="color"
                    className="w-32 h-12 p-1 rounded-lg bg-base-200 border border-base-300 cursor-pointer"
                    value={props.colorValue}
                    onChange={props.colorFunction}
                    >
                    </input>
                </fieldset>
            </div>
        </form> */}

        <BottomBar next="Continue" back="Cancel" formID="project-form" clickEvent={props.backEvent}/>
    </div>);
}