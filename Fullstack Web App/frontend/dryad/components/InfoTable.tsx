import { IconType } from "react-icons";

interface InfoTableProps {
    icon : IconType;
    title : string;
    keyValuePairs : {key : string, value : string}[];
}

export default function InfoTableProps(props: InfoTableProps) {
    const Icon = props.icon;
    return (<div className="rounded-xl w-full overflow-hidden border-white/5 border mt-5">
        <div className="flex flex-row items-center w-full border-b border-b-white/5 bg-base-200 p-4">
            <Icon className="text-accent text-lg mx-2"/>
            <h1 className="font-semibold">
                {props.title}
            </h1>
        </div>

        {props.keyValuePairs.map((pair, index)=>{
            return (
            <div className="flex flex-row items-center w-full border-b border-b-white/5 bg-secondary p-4 pl-6"
                key={index}>
                <p className="flex-1 text-secondary-content">
                    {pair.key}
                </p>
                <div className="flex flex-row flex-3 items-center   ">
                    {(pair.key=="Color") &&
                        <div className="h-4 w-4 mr-4 rounded-xs" style={{background : pair.value}}></div>
                    }
                    <p>
                        {pair.value}
                    </p>
                </div>
            </div>);
        })}
    </div>);
}