import { IconType } from "react-icons";

interface RoleBadgeProps {
    color : string;
    role : string;
    icon : IconType;
}

export default function RoleBadge(props : RoleBadgeProps) {
    const Icon = props.icon;
    return (
    <div className="mx-2 rounded-lg text-xs flex items-center gap-2 font-semibold px-2" 
    style={{color : props.color,
        backgroundColor : `${props.color}1A`
    }}>
        <Icon />
        {props.role}
    </div>);
}