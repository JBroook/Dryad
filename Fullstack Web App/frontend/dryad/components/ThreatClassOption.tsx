import { IconType } from "react-icons";
import { IoMdCheckmark } from "react-icons/io";

interface ThreatClassOptionProps {
  name : string;
  description : string;
  active : boolean;
  setActive : ()=>void;
  icon : IconType;
}

export default function ThreatClassOption(props : ThreatClassOptionProps) {
  const Icon = props.icon;
  return (
  <div className={props.active ? "bg-primary/15 rounded-xl p-4 flex flex-row justify-between items-center border border-width-[2px] border-accent/40 mb-2 cursor-pointer"
    :
    "bg-secondary rounded-xl p-4 flex flex-row justify-between items-center border border-width-[2px] border-white/8 mb-2 cursor-pointer"
  }
    onClick={props.setActive}>

    <div className="flex flex-row items-center">
      <Icon className={`text-xl ml-1 mr-4 ${props.active ? "text-accent" : "text-secondary-content"}`}/>
      <div>
          <h1 className={props.active ? "text-accent font-semibold text-base" : "font-semibold text-base"}>
              {props.name}
          </h1>
          <p className="text-secondary-content text-sm">
              {props.description}
          </p>
      </div>
    </div>

    {props.active &&
      <div className="rounded-full bg-accent text-white text-xl p-1">
        <IoMdCheckmark />
      </div>
    }
  </div>);
}