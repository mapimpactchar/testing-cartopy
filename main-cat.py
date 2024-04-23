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

HABITAT_CONDITION_COLOR_MAP = {
    (0, 1): '#b51963',
    (1, 2): '#ce2577',
    (2, 3): '#e6308a',
    (3, 4): '#d6f57c',
    (4, 5): '#b9da76',
    (5, 6): '#9bbf70',
    (6, 7): '#7ea56a',
    (7, 8): '#618a63',
    (8, 9): '#436f5d',
    (9, 10): '#265457',
}

HABITAT_COLUMN = 'BiodiversityCheck_H'
CONDITION_COLUMN = 'Condition'
HABITAT_CONDITION_COLUMN = 'Score_1to10'

BUFFER_X = 800
BUFFER_Y = 200

CONDITION_LEGEND_TITLE = 'Condition September 2023'

OUTPUT_DPI = 600

OSM_LEVEL = 17


def buffer_extents(extents, x_buffer, y_buffer):
    '''Buffer a bounding box in [x0, x1, y0, y1] format (matplotlib)'''
    return [
        extents[0] - x_buffer,
        extents[1] + x_buffer,
        extents[2] - y_buffer,
        extents[3] + y_buffer
    ]


def transpose_bounds(bounds):
    '''Transpose a bounding box from geopandas to matplotlib or vice versa'''
    return [bounds[0], bounds[2], bounds[1], bounds[3]]


def get_color_for_condition(condition_score):
    '''Get the color for the given condition score, defaulting to condition score 0'''
    return CONDITION_COLOR_MAP.get(condition_score, CONDITION_COLOR_MAP[0])


def render_condition_map(hex_layer,
                         boundary_layer,
                         contour_layer,
                         out_filename=None,
                         show_plot=False):
    '''Render the condition map'''
    print('Rendering condition map...')

    # Convert layer bounds to plot bounds (different orders) and add buffer.
    layer_bounds = hex_layer.total_bounds
    plot_bounds = buffer_extents(transpose_bounds(layer_bounds), BUFFER_X, BUFFER_Y)

    # Set up axes.
    ax = plt.axes(projection=ccrs.OSGB())
    ax.set_extent(plot_bounds, crs=ccrs.OSGB())

    # Add OSM layer to background.
    osm = OSM(desired_tile_form='L')
    ax.add_image(osm, OSM_LEVEL, cmap='gray', interpolation='spline36', regrid_shape=4000)

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

    # Render plot to image.
    if out_filename is not None:
        print(f'Outputting condition map to {out_filename}')
        plt.savefig(out_filename,
                    bbox_inches='tight',
                    pad_inches=0,
                    dpi=OUTPUT_DPI)

    # Show plot.
    if show_plot:
        print('Showing plot')
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


def render_habitat_map(hex_layer,
                       boundary_layer,
                       contour_layer,
                       out_filename=None,
                       show_plot=False):
    '''Render the habitat map'''
    print('Rendering habitat map...')

    # Convert layer bounds to plot bounds (different orders) and add buffer.
    layer_bounds = hex_layer.total_bounds
    plot_bounds = buffer_extents(transpose_bounds(layer_bounds), BUFFER_X, BUFFER_Y)

    # Set up axes.
    ax = plt.axes(projection=ccrs.OSGB())
    ax.set_extent(plot_bounds, crs=ccrs.OSGB())

    # Add OSM layer to background.
    osm = OSM(desired_tile_form='L')
    ax.add_image(osm, OSM_LEVEL, cmap='gray', interpolation='spline36', regrid_shape=4000)

    # Add hexes.
    for habitat in hex_layer[HABITAT_COLUMN].unique():
        # Filter hexes to habitat.
        hexes = hex_layer[hex_layer[HABITAT_COLUMN] == habitat]

        # Load icon for habitat.
        habitat_img = load_habitat_icon(habitat)

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

    # Render plot to image.
    if out_filename is not None:
        print(f'Outputting habitat map to {out_filename}')
        plt.savefig(out_filename,
                    bbox_inches='tight',
                    pad_inches=0,
                    dpi=OUTPUT_DPI)

    # Show plot.
    if show_plot:
        print('Showing plot')
        plt.show()


def get_color_for_habitat_condition(score_1_to_10):
    # Find the matching color for the given score.
    for (min_score, max_score), color in HABITAT_CONDITION_COLOR_MAP.items():
        if min_score < score_1_to_10 and score_1_to_10 <= max_score:
            return color

    # Return the last color by default if none match.
    return color


def render_habitat_condition_map(hex_layer,
                                 boundary_layer,
                                 contour_layer,
                                 out_filename=None,
                                 show_plot=False):
    '''Render the habitat condition map'''
    print('Rendering habitat condition map...')

    # Convert layer bounds to plot bounds (different orders) and add buffer.
    layer_bounds = hex_layer.total_bounds
    plot_bounds = buffer_extents(transpose_bounds(layer_bounds), BUFFER_X, BUFFER_Y)

    # Set up axes.
    ax = plt.axes(projection=ccrs.OSGB())
    ax.set_extent(plot_bounds, crs=ccrs.OSGB())

    # Add OSM layer to background.
    osm = OSM(desired_tile_form='L')
    ax.add_image(osm, OSM_LEVEL, cmap='gray', interpolation='spline36', regrid_shape=4000)

    # Add hexes.
    for score_1_to_10 in hex_layer[HABITAT_CONDITION_COLUMN].unique():
        hexes = hex_layer[hex_layer[HABITAT_CONDITION_COLUMN] == score_1_to_10]
        facecolor = get_color_for_habitat_condition(score_1_to_10)

        ax.add_geometries(hexes['geometry'],
                          crs=hex_layer.crs,
                          facecolor=facecolor,
                          edgecolor='none',
                          linestyle='-',
                          linewidth=0.26)

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

    # Render plot to image.
    if out_filename is not None:
        print(f'Outputting habitat map to {out_filename}')
        plt.savefig(out_filename,
                    bbox_inches='tight',
                    pad_inches=0,
                    dpi=OUTPUT_DPI)

    # Show plot.
    if show_plot:
        print('Showing plot')
        plt.show()


def render_habitat_condition_graph(hex_layer,
                                   out_filename=None,
                                   show_plot=False):
    '''Render the habitat condition graph'''
    print('Rendering habitat condition graph...')

    # Calculate the area in hectares for a score range.
    def calculate_area_for_score_range(min_score, max_score):
        # Get the rows in range.
        rows_in_range = hex_layer[HABITAT_CONDITION_COLUMN] \
            .between(min_score, max_score, inclusive='right')

        # Calculate the area of all the hexes.
        area = hex_layer[rows_in_range].geometry.area.sum()

        # Convert to hectares.
        return area / 10000.0

    # Calculate each bar area_ha and color.
    def get_area_and_color(key_value):
        (min_score, max_score), color = key_value
        area_ha = calculate_area_for_score_range(min_score, max_score)
        return (max_score, area_ha, color)

    # Format hectares value to string.
    def format_hectares(area_ha):
        if area_ha < 10:
            return f'{area_ha:.2f} ha'
        else:
            return f'{area_ha:.1f} ha'

    # Pre-calculate bars.
    bars = list(map(get_area_and_color, HABITAT_CONDITION_COLOR_MAP.items()))
    max_area = max(map(lambda x: x[1], bars))

    # Start the chart.
    fig, ax = plt.subplots()

    ax.axis('off')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_yticks([])

    # Add bars.
    for i, bar in enumerate(bars):
        score, area_ha, color = bar

        # Background bar.
        ax.barh(score, max_area, color='#eee')

        # Data bar.
        ax.barh(score, area_ha, color=color)

        # Left label (score).
        ax.text(0, score, str(score),
                verticalalignment='center',
                horizontalalignment='right')

        # Right label (area ha).
        ax.text(max_area, score, format_hectares(area_ha),
                verticalalignment='center',
                horizontalalignment='left')

    # Add high and low axis labels.
    ax.text(0.0, 1, 'High', verticalalignment='center', horizontalalignment='right')
    ax.text(0.0, len(bars), 'Low', verticalalignment='center', horizontalalignment='right')

    # Render plot to image.
    if out_filename is not None:
        print(f'Outputting habitat condition graph to {out_filename}')
        plt.savefig(out_filename,
                    bbox_inches='tight',
                    pad_inches=0,
                    dpi=OUTPUT_DPI)

    # Show plot.
    if show_plot:
        plt.show()


def main():
    # Load in files.
    hex_layer = gpd.read_file('data/Final_shapefile.gpkg', engine='pyogrio')
    boundary_layer = gpd.read_file('./data/Royal Alexandra & Albert School.shp', engine='pyogrio')
    contour_layer = gpd.read_file('./data/contours.gpkg', boundary_layer, engine='pyogrio')

    render_condition_map(hex_layer,
                         boundary_layer,
                         contour_layer,
                         out_filename='condition_map.png',
                         show_plot=False)

    render_habitat_map(hex_layer,
                       boundary_layer,
                       contour_layer,
                       out_filename='habitat_map.png',
                       show_plot=False)

    render_habitat_condition_map(hex_layer,
                                 boundary_layer,
                                 contour_layer,
                                 out_filename='habitat_condition.png',
                                 show_plot=False)

    render_habitat_condition_graph(hex_layer,
                                   out_filename='habitat_condition_graph.png',
                                   show_plot=False)

    print('Done!')


if __name__ == "__main__":
    main()
