import { IconType } from "react-icons";

interface StepProps {
    title : string;
    step : number;
    icon : IconType;
}

export default function CurrentStep(props: StepProps) {
    const Icon = props.icon;
    return (
        <div className="rounded-xl border border-primary bg-base-300 flex flex-row items-center w-full mb-2 px-2 py-4">
            <Icon className="text-xl mx-4  text-accent"/>
            <div>
                <p className="text-sm text-secondary-content">Step {props.step+1}</p>
                <h1 className="font-semibold text-accent">{props.title}</h1>
            </div>
        </div>);
}