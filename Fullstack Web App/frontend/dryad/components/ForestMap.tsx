"use client"

import L from 'leaflet';
import { MapContainer, TileLayer, useMap } from 'react-leaflet'

interface ForestMapProps {
    searchValue : string;
    latitude : string;
    longitude : string;
}

export default function ForestMap(props: ForestMapProps) {
    const position = L.latLng(52.51, 13.38);

    function MapController (){
        const map = useMap();
        const position = L.latLng(parseFloat(props.latitude), parseFloat(props.longitude));

        map.setView(position, 13);

        return null;
    }

    return ( 
    <div className="map w-full h-[500px]">
        <MapContainer 
            center={position} 
            zoom={6} 
            scrollWheelZoom={true}>
            <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <MapController />
        </MapContainer>
    </div>);
}