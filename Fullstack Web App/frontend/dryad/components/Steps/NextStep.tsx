import { IconType } from "react-icons";

interface StepProps {
    title : string;
    step : number;
    icon : IconType;
}

export default function NextStep(props: StepProps) {
    const Icon = props.icon;
    return (
        <div className="rounded-xl flex flex-row items-center w-full mb-2 px-2 py-4 opacity-20">
            <Icon className="text-xl mx-4  text-secondary-content"/>
            <div>
                <p className="text-sm text-secondary-content">Step {props.step+1}</p>
                <h1 className="font-semibold">{props.title}</h1>
            </div>
        </div>);
}