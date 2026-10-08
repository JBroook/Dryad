import { IconType } from "react-icons";

interface NotificationOptionProps {
    title : string;
    description : string;
    icon : IconType;
    state : boolean;
    onChange : ()=>void;
}

export default function NotificationOption(props : NotificationOptionProps) {
    const Icon = props.icon;
    return (
    <div className="flex items-center">
        <Icon className="text-accent text-2xl mr-4"/>
        <div className="flex-1">
            <h1 className="font-semibold text-lg">{props.title}</h1>
            <p className="text-secondary-content text-base">{props.description}</p>
        </div>
        <input type="checkbox" defaultChecked className="toggle toggle-primary" />
    </div>);
}