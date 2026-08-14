"use client"

import L from 'leaflet';
import { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet'

interface ForestMapProps {
    searchValue : string;
    latitude : number;
    longitude : number;
}

export default function ForestMap(props: ForestMapProps) {
    const position = L.latLng(52.51, 13.38);

    function MapController({ location }: { 
        location: { lat: number; lon: number } | null 
    }) {
        const map = useMap();

        useEffect(() => {
            if (location) {
                map.setView(
                    [location.lat, location.lon],
                    13
                );
            }
        }, [location, map]);

        return null;
    }
    return ( 
    <div className="map w-full h-[500px] rounded-md overflow-hidden z-0">
        <MapContainer 
            center={position} 
            zoom={6} 
            scrollWheelZoom={true}>
            <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <MapController location={{lat : props.latitude, lon : props.longitude}} />
        </MapContainer>
    </div>);
}