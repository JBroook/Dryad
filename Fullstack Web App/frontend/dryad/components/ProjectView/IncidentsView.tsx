import { HiOutlineFilter } from "react-icons/hi";
import Incident from "../Incident";
import { FaTruck } from "react-icons/fa";

interface IncidentsViewProps {
    filterOptions : string[];
    filterIndex : number;
    setFilterIndex : (index : number) => void;
}

export default function IncidentsView(props: IncidentsViewProps) {
    return (<>
    <div className="ml-6 flex flex-row items-center mt-5">
        <HiOutlineFilter className="text-secondary-content text-lg"/>
        {props.filterOptions.map((filterOption, index)=>{
        return (
        <button 
            className={index!=props.filterIndex ? "btn btn-base-200 text-secondary-content border border-white/5 ml-2" :
            "btn bg-[#0A2513] text-accent border border-accent/50 ml-2"
            }
            key={index}
            onClick={()=>props.setFilterIndex(index)}>
            {filterOption}
        </button>)
        })}
    </div>

    <div className="mx-6 mt-5">
        <Incident 
            color="#F97316"
            icon={FaTruck}
            name="Logging Vehicle"
            location="-3.8100°, -52.3800°"
            date="June 12"
            time="6/12/2026, 4:23:11 PM"
            device="A-15"
            confidence={96}
        />
        <Incident 
            color="#F97316"
            icon={FaTruck}
            name="Logging Vehicle"
            location="-3.8100°, -52.3800°"
            date="June 12"
            time="6/12/2026, 4:23:11 PM"
            device="A-15"
            confidence={96}
        />
    </div>
    </>);
}