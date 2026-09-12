import { FaCircle } from "react-icons/fa";
import { FaLocationDot } from "react-icons/fa6";
import { MdNavigateNext, MdOutlineLocationOn } from "react-icons/md";
import HollowCard from "./HollowCard";

interface ProjectCardProps {
  tag : string;
  name : string;
  region : string;
  area : number;
  alerts : number;
  activeDevices : number;
  totalDevices : number;
  members : number;
  accentColor : string;
  tagColor: string;
  openProject : ()=>void;
}

export default function ProjectCard(props : ProjectCardProps) {
    return (
    <div className={`
      relative
      overflow-hidden
      rounded-2xl
      p-6
      before:absolute
      before:inset-x-0
      before:top-0
      before:h-2
      before:bg-[var(--accent-color)]
      border border-white/8 border-width-[2px]
      cursor-pointer
      hover:bg-base-300
      bg-base-200
      flex flex-col
    `}
    style={{
      "--accent-color": props.accentColor,
    } as React.CSSProperties}
    onClick={()=>props.openProject()}
    >
      <div className="flex-1">
        <div className="w-full flex justify-between items-center">
          <div className="badge bg-base-300 mb-2" style={{
            color:props.tagColor,
            backgroundImage: "none",}}>
            • {props.tag}
          </div>

          <MdNavigateNext className="text-xl text-secondary-content"/>
        </div>
        <h2 className="text-xl font-bold">{props.name}</h2>
        <p className="text-secondary-content">
          <MdOutlineLocationOn className="inline-block align-middle mr-1" />
          {props.region} • {props.area}km²
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 mt-3">
        <HollowCard className="flex flex-col justify-center items-center py-2 border-none">
          <h2 className="font-semibold text-warning text-lg">
            {props.alerts}
          </h2>
          <p className="text-secondary-content text-xs">
            New Alerts
          </p>
        </HollowCard>

        <HollowCard className="flex flex-col justify-center items-center py-2 border-none">
          <h2 className="font-semibold text-lg">
            {props.activeDevices}/{props.totalDevices}
          </h2>
          <p className="text-secondary-content text-xs">
            Devices
          </p>
        </HollowCard>

        <HollowCard className="flex flex-col justify-center items-center py-2 border-none">
          <h2 className="font-semibold text-lg">
            {props.members}
          </h2>
          <p className="text-secondary-content text-xs">
            Members
          </p>
        </HollowCard>
      </div>
    </div>);
}