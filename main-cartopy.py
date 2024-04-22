import matplotlib.pyplot as plt
from cartopy.io.img_tiles import OSM
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd


def main():
    # --- setup ---
    # Create OSM instance
    osm = OSM(desired_tile_form='L')

    # creating axes for the plot with EPSG:27700 (in cartopy this is: ccrs.OSGB())
    # rect = [10, 10, 10, 10] # = [200, 200, 200, 200]
    ax = plt.axes(projection=ccrs.OSGB()) # plt.axes(rect, projection=ccrs.OSGB())
    # fig = plt.figure(figsize=(10, 10))
    # ax = fig.add_subplot(1, 1, 1, projection=ccrs.OSGB())

    # --- read in the layer files ---
    # read in the final shapefile (hexes)
    hex_layer = gpd.read_file('./data/Final_Shapefile.gpkg', engine="pyogrio")

    # setting the extent from the hex layer boundaries
    x_buffer = 800  # to help create the rectangle around the extent of the data layers
    y_buffer = 200
    extent = hex_layer.total_bounds
    # extent_list = [extent[0], extent[2], extent[1], extent[3]]
    extent_list = [extent[0] - x_buffer, extent[2] + x_buffer, extent[1] - y_buffer, extent[3] + y_buffer]
    # setting an extent for the plot
    ax.set_extent(extent_list, crs=ccrs.OSGB())

    # read in the boundary (AOI) data
    boundary_layer = gpd.read_file('./data/Royal Alexandra & Albert School.shp', engine="pyogrio")
    # read in the contour data
    contour_layer = gpd.read_file('./data/countrywide_map_layer.shp', engine="pyogrio")


    # --- read in the style files ---

    
    # --- creating cartopy features ---
    hex_geometries = list(hex_layer.geometry)
    hex_feature = cfeature.ShapelyFeature(hex_geometries, crs=ccrs.OSGB(), facecolor='#457276', edgecolor='#808080', linewidth=0.3, zorder=2)
    boundary_geometries = list(boundary_layer.geometry)
    boundary_feature = cfeature.ShapelyFeature(boundary_geometries, crs=ccrs.OSGB(), facecolor='none', edgecolor='#d7191c', linestyle="-", linewidth=0.46, zorder=3)
    contour_geometries = list(contour_layer.geometry)
    contour_feature = cfeature.ShapelyFeature(contour_geometries, crs=ccrs.OSGB(), facecolor='none', edgecolor='#bdbdbd', linestyle="-", linewidth=0.26, alpha=0.5, zorder=1)


    # --- plotting the data ---
    # adding the osm basemap layer (cmap as gray along with desired_tile_form as L => grayscale)
    zoom_level = 18
    ax.add_image(osm, zoom_level, cmap='gray')

    ax.add_feature(hex_feature)
    ax.add_feature(boundary_feature)
    ax.add_feature(contour_feature)


    # plot the contour data with matplotlib
    # contour_layer.plot(ax=ax, edgecolor='black', linewidth=0.5, zorder=1)  # takes 2 mins for the contours
    # # plot the final shapefile
    # hex_layer.plot(ax=ax, zorder=2)
    # # plot the boundary (AOI) data
    # boundary_layer.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=0.5, zorder=3)
    

    # TODO: style the vector layers correctly

    # Save the figure and remove all whitespace from the png
    dpi_value = 1000
    plt.savefig(f"dpi-{dpi_value}-with-zoom-{zoom_level}.png",bbox_inches='tight', pad_inches = 0, dpi=dpi_value)

    # Show the plot
    plt.show()

if __name__ == "__main__":
    main()
