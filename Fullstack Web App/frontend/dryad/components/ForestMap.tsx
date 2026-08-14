"use client"

import L from 'leaflet';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'

interface ForestMapProps {
}

export default function ForestMap(props: ForestMapProps) {
    const position = L.latLng(52.51, 13.38);

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
        </MapContainer>
    </div>);
}