import { IconType } from "react-icons";

interface Props {
    icon : IconType;
    colorOne : string;
    colorTwo : string;
    colorThree : string;
    name : string;
    onClick : ()=>void;
    active : boolean;
}

export default function ThemeButton(props : Props) {
    const Icon = props.icon

    return (
    <>
    <div className={`flex-1 rounded-2xl flex 
    flex-col items-center justify-center p-2 cursor-pointer ${props.active ? "border border-accent bg-base-300" : "border border-white/15 bg-base-200"}`}
    onClick={props.onClick}>
        <div className="flex gap-2 w-full px-4 my-2">
        <div className="flex-1 h-4 rounded-sm" style={{backgroundColor : props.colorOne}}>

        </div>
        <div className="flex-1 h-4 rounded-sm" style={{backgroundColor : props.colorTwo}}>

        </div>
        <div className="flex-1 h-4 rounded-sm" style={{backgroundColor : props.colorThree}}>

        </div>
        </div>
        <div className={`flex my-2 ${!props.active && "text-secondary-content"}`}>
            <Icon className="text-xl mr-3"/>
            <p className="font-semibold">{props.name}</p>
        </div>
    </div>
    </>);
}