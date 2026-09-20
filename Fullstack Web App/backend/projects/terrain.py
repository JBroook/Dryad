import os
import numpy as np
import requests
import rasterio

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