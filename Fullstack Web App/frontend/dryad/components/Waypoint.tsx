import { TbTrash } from "react-icons/tb";

interface Props {
    count : number;
    coords : string;
    deleteEvent : ()=>void;
}

export default function Waypoint(props : Props) {
    return (
    <div className="flex mt-2 items-center">
        <h1 className="font-bold mr-3">
            {props.count}. 
        </h1>
        <p>{props.coords}</p>
        <button className="btn btn-error p-2 ml-auto" onClick={props.deleteEvent}>
            <TbTrash className="text-xl"/>
        </button>
    </div>);
}