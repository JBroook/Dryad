import { IconType } from "react-icons";
import { IoMdCheckmark } from "react-icons/io";

interface StepProps {
    title : string;
    step : number;
    icon : IconType;
}

export default function CompletedStep(props: StepProps) {
    const Icon = props.icon;
    return (
        <div className="rounded-xl bg-base-300 flex flex-row items-center w-full mb-2 px-2 py-4">
            <IoMdCheckmark className="text-xl mx-4 text-accent"/>
            <div>
                <p className="text-sm text-secondary-content">Step {props.step+1}</p>
                <h1 className="font-semibold">{props.title}</h1>
            </div>
        </div>);
}