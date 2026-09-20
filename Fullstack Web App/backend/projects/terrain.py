import os
import numpy as np
import requests
import rasterio
from django.contrib.gis.geos import LineString
from .models import OSMRoad
from django.contrib.gis.db.models.functions import Distance, Transform

def get_project_bbox(project):
    bbox = project.monitoring_area.extent

    xmin, ymin, xmax, ymax = bbox

    return {
        "west": xmin,
        "south": ymin,
        "east": xmax,
        "north": ymax,
    }

def download_dem(project, output_path):
    api_key = os.getenv("OPENTOPOGRAPHY_KEY")

    bbox = get_project_bbox(project)

    url = "https://portal.opentopography.org/API/globaldem"

    params = {
        "demtype": "COP30",

        "south": bbox["south"],
        "north": bbox["north"],
        "west": bbox["west"],
        "east": bbox["east"],

        "outputFormat": "GTiff",

        "API_Key": api_key,
    }

    response = requests.get(
        url,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

def populate_terrain_data(project, dem_path, slope_path):
    with rasterio.open(dem_path) as dem, \
     rasterio.open(slope_path) as slope:

        for cell in project.grid_cells.all():
            centroid = cell.geometry.centroid

            x = centroid.x
            y = centroid.y

            elevation = next(
                dem.sample([(x, y)])
            )[0]

            slope_value = next(
                slope.sample([(x, y)])
            )[0]

            cell.elevation = float(elevation)
            cell.slope = float(slope_value)

            cell.save(
                update_fields=[
                    "elevation",
                    "slope"
                ]
            )

def generate_slope_raster(dem_path, slope_path):

    with rasterio.open(dem_path) as src:

        elevation = src.read(1)

        profile = src.profile

        x_res = src.res[0]
        y_res = src.res[1]

        # Calculate elevation gradients
        dz_dx = np.gradient(
            elevation,
            x_res,
            axis=1
        )

        dz_dy = np.gradient(
            elevation,
            y_res,
            axis=0
        )

        # Calculate slope in radians
        slope_radians = np.arctan(
            np.sqrt(
                dz_dx ** 2 +
                dz_dy ** 2
            )
        )

        # Convert radians → degrees
        slope_degrees = np.degrees(slope_radians)

        profile.update(
            dtype=rasterio.float32,
            count=1,
            nodata=-9999
        )

        with rasterio.open(
            slope_path,
            "w",
            **profile
        ) as dst:

            dst.write(
                slope_degrees.astype(rasterio.float32),
                1
            )


def download_osm_roads(project):
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    bbox = get_project_bbox(project)

    query = f"""
    [out:json];

    way["highway"](
        {bbox["south"]},
        {bbox["west"]},
        {bbox["north"]},
        {bbox["east"]}
    );

    out geom;
    """

    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={
            "User-Agent": "Dryad/1.0 (forest monitoring FYP)"
        },
        timeout=120
    )

    print("Overpass status:", response.status_code)
    print("Overpass response:", response.text[:1000])

    response.raise_for_status()

    return response.json()


def save_osm_roads(data):
    roads = []

    for element in data["elements"]:

        if element["type"] != "way":
            continue

        geometry = element.get("geometry")

        if not geometry or len(geometry) < 2:
            continue

        coordinates = [
            (point["lon"], point["lat"])
            for point in geometry
        ]

        road = OSMRoad(
            osm_id=element["id"],
            geometry=LineString(
                coordinates,
                srid=4326
            )
        )

        roads.append(road)

    OSMRoad.objects.bulk_create(
        roads,
        ignore_conflicts=True
    )


def populate_road_distances(project):
    roads = OSMRoad.objects.all().annotate(
        projected_geometry=Transform(
            "geometry",
            32647
        )
    )

    for cell in project.grid_cells.all():

        cell_geometry = cell.geometry.transform(
            32647,
            clone=True
        )

        nearest = (
            roads
            .annotate(
                distance=Distance(
                    "projected_geometry",
                    cell_geometry
                )
            )
            .order_by("distance")
            .first()
        )

        if nearest:
            cell.distance_to_road = nearest.distance.m
            cell.save(update_fields=["distance_to_road"])