import sys

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms

from matplotlib.image import BboxImage
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.path import Path

from descartes.patch import PolygonPatch

from cartopy.io.img_tiles import OSM
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import numpy
import shapely


CONDITION_COLOR_MAP = {
    0: '#00441b',
    1: '#f7fcf5',
    2: '#b2e0ab',
    3: '#3da75a',
}

CONDITION_LABELS = {
    0: 'Unknown',
    1: 'Poor or Not Applicable',
    2: 'Moderate',
    3: 'Good',
}

HABITAT_COLUMN = 'BiodiversityCheck_H'
CONDITION_COLUMN = 'Condition'

CONDITION_LEGEND_TITLE = 'Condition September 2023'


def buffer_extents(layer, x_buffer, y_buffer):
    extents = layer.total_bounds
    return [
        extents[0] - x_buffer,
        extents[2] + x_buffer,
        extents[1] - y_buffer,
        extents[3] + y_buffer
    ]


def get_color_for_condition(condition_score):
    '''Get the color for the given condition score, defaulting to condition score 0'''
    return CONDITION_COLOR_MAP.get(condition_score, CONDITION_COLOR_MAP[0])


def render_condition_map(hex_layer, boundary_layer, contour_layer, show_plot=False, save_png=False):
    '''Render the condition map'''
    # Set up axes.
    ax = plt.axes(projection=ccrs.OSGB())
    ax.set_extent(buffer_extents(hex_layer, 800, 200), crs=ccrs.OSGB())

    # Add OSM layer to background.
    osm = OSM(desired_tile_form='L')
    zoom_level = 18
    ax.add_image(osm, zoom_level, cmap='gray')

    # Create list for legend layers.
    legend_layers = []
    legend_labels = []

    # Add hexes.
    for condition in hex_layer[CONDITION_COLUMN].unique():
        hexes = hex_layer[hex_layer[CONDITION_COLUMN] == condition]
        facecolor = get_color_for_condition(condition)

        ax.add_geometries(hexes['geometry'],
                          crs=hex_layer.crs,
                          facecolor=facecolor,
                          edgecolor="black",
                          linestyle='-',
                          linewidth=0.26)

        legend_label = CONDITION_LABELS.get(condition)
        if legend_label:
            legend_layers.append(mpatches.Rectangle((0, 0), 1, 1, facecolor=facecolor))
            legend_labels.append(legend_label)

    # Add boundary.
    boundary_geometries = list(boundary_layer.geometry)
    boundary_feature = cfeature.ShapelyFeature(boundary_geometries,
                                               crs=ccrs.OSGB(),
                                               facecolor='none',
                                               edgecolor='#d7191c',
                                               linestyle="-",
                                               linewidth=0.46,
                                               zorder=3)
    ax.add_feature(boundary_feature)

    # Add contours.
    contour_geometries = list(contour_layer.geometry)
    contour_feature = cfeature.ShapelyFeature(contour_geometries,
                                              crs=ccrs.OSGB(),
                                              facecolor='none',
                                              edgecolor='#bdbdbd',
                                              linestyle="-",
                                              linewidth=0.26,
                                              alpha=0.5,
                                              zorder=1)
    ax.add_feature(contour_feature)

    # Add legend.
    ax.legend(handles=legend_layers, labels=legend_labels, title=CONDITION_LEGEND_TITLE)

    # Save png.
    if save_png:
        dpi_value = 1000
        zoom_level = 19
        output_path = f"./outputs/condition-map-with-dpi-{dpi_value}-and-zoom-{zoom_level}.png"
        plt.savefig(output_path, bbox_inches='tight', pad_inches = 0, dpi=dpi_value)

    # Show plot.
    if show_plot:
        plt.show()


def load_habitat_icon(habitat_name):
    return plt.imread(f'style_files/habitats_symbology/{habitat_name}.png')


def geom_to_path(geom):
    # Convert MultiPolygon to Polygon
    if geom.geom_type == 'MultiPolygon':
        geom = geom.buffer(0)

    # Get polygon coords and construct Path.
    coords = geom.exterior.coords
    return Path(coords)


def render_habitat_map(hex_layer, boundary_layer, contour_layer, show_plot=False, save_png=False):
    '''Render the habitat map'''
    # Set up axes.
    ax = plt.axes(projection=ccrs.OSGB())
    ax.set_extent(buffer_extents(hex_layer, 800, 200), crs=ccrs.OSGB())

    # Add OSM layer to background.
    osm = OSM(desired_tile_form='L')
    zoom_level = 18
    ax.add_image(osm, zoom_level, cmap='gray')

    # Add hexes.
    for habitat in hex_layer[HABITAT_COLUMN].unique():
        # Filter hexes to habitat.
        hexes = hex_layer[hex_layer[HABITAT_COLUMN] == habitat]

        # Load icon for habitat.
        habitat_img = load_habitat_icon(habitat)

        # Add outlines.
        ax.add_geometries(hexes['geometry'],
                          crs=hex_layer.crs,
                          facecolor="None",
                          edgecolor="black",
                          linestyle='-',
                          linewidth=0.26,
                          zorder=50)

        # Add icons.
        for geom in hexes.geometry:
            centroid = geom.centroid

            # Get bounds of geometry to draw image to, and flip them from (x0, y0, x1, y1)
            # to (x0, x1, y0, y1) for matplotlib.
            bounds = geom.bounds
            bounds = [bounds[0], bounds[2], bounds[1], bounds[3]]

            # Add image.
            im = ax.imshow(habitat_img, extent=bounds, zorder=25)

            # Clip to geometry.
            im.set_clip_path(geom_to_path(geom), transform=ax.transData)

    # Add boundary.
    boundary_geometries = list(boundary_layer.geometry)
    boundary_feature = cfeature.ShapelyFeature(boundary_geometries,
                                               crs=ccrs.OSGB(),
                                               facecolor='none',
                                               edgecolor='#d7191c',
                                               linestyle="-",
                                               linewidth=0.46,
                                               zorder=3)
    ax.add_feature(boundary_feature)

    # Add contours.
    contour_geometries = list(contour_layer.geometry)
    contour_feature = cfeature.ShapelyFeature(contour_geometries,
                                              crs=ccrs.OSGB(),
                                              facecolor='none',
                                              edgecolor='#bdbdbd',
                                              linestyle="-",
                                              linewidth=0.26,
                                              alpha=0.5,
                                              zorder=1)
    ax.add_feature(contour_feature)

    # Save png.
    if save_png:
        dpi_value = 1000
        zoom_level = 19
        output_path = f"./outputs/habitat-map-with-dpi-{dpi_value}-and-zoom-{zoom_level}.png"
        plt.savefig(output_path, bbox_inches='tight', pad_inches = 0, dpi=dpi_value)

    # Show plot.
    if show_plot:
        plt.show()


def main():
    # Load in files.
    hex_layer = gpd.read_file('data/Final_shapefile.gpkg', engine='pyogrio')
    boundary_layer = gpd.read_file('./data/Royal Alexandra & Albert School.shp', engine='pyogrio')
    contour_layer = gpd.read_file('./data/contours.gpkg', boundary_layer, engine='pyogrio')

    #render_condition_map(hex_layer, boundary_layer, contour_layer, show_plot=True, save_png=True)
    render_habitat_map(hex_layer, boundary_layer, contour_layer, show_plot=True, save_png=True)


if __name__ == "__main__":
    main()
