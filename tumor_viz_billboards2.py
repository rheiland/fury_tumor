from fury import actor, ui, window
from pyMCDS_cells import pyMCDS_cells


import glob
import numpy as np
import os
import vtk


_PATH_DIR = os.path.abspath(os.path.dirname('__file__'))
_DATA_DIR = os.path.join(_PATH_DIR, 'data')
_RANGE_CENTERS = \
    """
    uniform vec3 lowRanges;
    uniform vec3 highRanges;
    
    bool isVisible(vec3 center)
    {
        bool xValidation = lowRanges.x <= center.x && center.x <= highRanges.x;
        bool yValidation = lowRanges.y <= center.y && center.y <= highRanges.y;
        bool zValidation = lowRanges.z <= center.z && center.z <= highRanges.z;
        return xValidation || yValidation || zValidation;
    }
    """
_FAKE_SPHERE = \
    """
    if(!isVisible(centerVertexMCVSOutput))
        discard;
    float len = length(point);
    float radius = 1.;
    if(len > radius)
        discard;
    vec3 normalizedPoint = normalize(vec3(point.xy, sqrt(1. - len)));
    vec3 direction = normalize(vec3(1., 1., 1.));
    float df_1 = max(0, dot(direction, normalizedPoint));
    float sf_1 = pow(df_1, 24);
    fragOutput0 = vec4(max(df_1 * color, sf_1 * vec3(1)), 1);
    """


def build_label(text, font_size=18, bold=False):
    label = ui.TextBlock2D()
    label.message = text
    label.font_size = font_size
    label.font_family = 'Arial'
    label.justification = 'left'
    label.bold = bold
    label.italic = False
    label.shadow = False
    label.actor.GetTextProperty().SetBackgroundColor(0, 0, 0)
    label.actor.GetTextProperty().SetBackgroundOpacity(0.0)
    label.color = (1, 1, 1)
    return label


def change_clipping_plane_x(slider):
    global high_perc, high_ranges, low_perc, low_ranges, max_centers, min_centers
    values = slider._values
    r1, r2 = values
    low_ranges[0] = r1
    high_ranges[0] = r2
    range_centers = max_centers[0] - min_centers[0]
    low_perc[0] = (r1 - min_centers[0]) / range_centers * 100
    high_perc[0] = (r2 - min_centers[0]) / range_centers * 100


def change_clipping_plane_y(slider):
    global high_perc, high_ranges, low_perc, low_ranges, max_centers, min_centers
    values = slider._values
    r1, r2 = values
    low_ranges[1] = r1
    high_ranges[1] = r2
    range_centers = max_centers[1] - min_centers[1]
    low_perc[1] = (r1 - min_centers[1]) / range_centers * 100
    high_perc[1] = (r2 - min_centers[1]) / range_centers * 100


def change_clipping_plane_z(slider):
    global high_perc, high_ranges, low_perc, low_ranges, max_centers, min_centers
    values = slider._values
    r1, r2 = values
    low_ranges[2] = r1
    high_ranges[2] = r2
    range_centers = max_centers[2] - min_centers[2]
    low_perc[2] = (r1 - min_centers[2]) / range_centers * 100
    high_perc[2] = (r2 - min_centers[2]) / range_centers * 100


def change_frame(slider):
    global idx_xml
    idx_xml = int(slider.value)
    update_frame()


def read_data():
    global idx_xml, xml_files

    mcds = pyMCDS_cells(xml_files[idx_xml], _DATA_DIR)

    ncells = len(mcds.data['discrete_cells']['ID'])

    centers = np.zeros((ncells, 3))
    centers[:, 0] = mcds.data['discrete_cells']['position_x']
    centers[:, 1] = mcds.data['discrete_cells']['position_y']
    centers[:, 2] = mcds.data['discrete_cells']['position_z']

    colors = np.zeros((ncells, 3))
    colors[:, 0] = 1
    colors[:, 1] = 1
    colors[:, 2] = 0

    cycle_model = mcds.data['discrete_cells']['cycle_model']

    cell_type = mcds.data['discrete_cells']['cell_type']

    onco = mcds.data['discrete_cells']['oncoprotein']
    onco_min = onco.min()
    onco_range = onco.max() - onco.min()

    # This coloring is only approximately correct, but at least it shows
    # variation in cell colors
    for idx in range(ncells):
        if cell_type[idx] == 1:
            colors[idx, 0] = 1
            colors[idx, 1] = 1
            colors[idx, 2] = 0
        if cycle_model[idx] < 100:
            colors[idx, 0] = 1.0 - (onco[idx] - onco_min) / onco_range
            colors[idx, 1] = colors[idx, 0]
            colors[idx, 2] = 0
        elif cycle_model[idx] == 100:
            colors[idx, 0] = 1
            colors[idx, 1] = 0
            colors[idx, 2] = 0
        elif cycle_model[idx] > 100:
            colors[idx, 0] = 0.54  # 139./255
            colors[idx, 1] = 0.27  # 69./255
            colors[idx, 2] = 0.075  # 19./255

    radius = mcds.data['discrete_cells']['total_volume'] * .75 / np.pi
    radius = np.cbrt(radius)

    return centers, colors, radius


def update_frame():
    global high_perc, high_ranges, low_perc, low_ranges, max_centers, \
        min_centers, scene, spheres_actor, slider_clipping_plane_thrs_x, \
        slider_clipping_plane_thrs_y, slider_clipping_plane_thrs_z

    slider_clipping_plane_thrs_x.on_change = lambda slider: None
    slider_clipping_plane_thrs_y.on_change = lambda slider: None
    slider_clipping_plane_thrs_z.on_change = lambda slider: None

    centers, colors, radius = read_data()

    scene.rm(spheres_actor)

    spheres_actor = actor.billboard(
        centers, colors, scales=radius, fs_dec=_RANGE_CENTERS,
        fs_impl=_FAKE_SPHERE)

    spheres_mapper = spheres_actor.GetMapper()
    spheres_mapper.AddObserver(vtk.vtkCommand.UpdateShaderEvent,
                               vtk_shader_callback)

    scene.add(spheres_actor)

    min_centers = np.min(centers, axis=0)
    max_centers = np.max(centers, axis=0)

    low_ranges = np.array(
        [np.percentile(centers[:, i], v) for i, v in enumerate(low_perc)]
    )
    high_ranges = np.array(
        [np.percentile(centers[:, i], v) for i, v in enumerate(high_perc)]
    )

    slider_clipping_plane_thrs_x.left_disk_value = low_ranges[0]
    slider_clipping_plane_thrs_x.right_disk_value = high_ranges[0]
    slider_clipping_plane_thrs_x.min_value = min_centers[0]
    slider_clipping_plane_thrs_x.max_value = max_centers[0]
    slider_clipping_plane_thrs_x.on_change = change_clipping_plane_x

    slider_clipping_plane_thrs_y.left_disk_value = low_ranges[1]
    slider_clipping_plane_thrs_y.right_disk_value = high_ranges[1]
    slider_clipping_plane_thrs_y.min_value = min_centers[1]
    slider_clipping_plane_thrs_y.max_value = max_centers[1]
    slider_clipping_plane_thrs_y.on_change = change_clipping_plane_y

    slider_clipping_plane_thrs_z.left_disk_value = low_ranges[2]
    slider_clipping_plane_thrs_z.right_disk_value = high_ranges[2]
    slider_clipping_plane_thrs_z.min_value = min_centers[2]
    slider_clipping_plane_thrs_z.max_value = max_centers[2]
    slider_clipping_plane_thrs_z.on_change = change_clipping_plane_z


@vtk.calldata_type(vtk.VTK_OBJECT)
def vtk_shader_callback(caller, event, calldata=None):
    global high_ranges, low_ranges
    if calldata is not None:
        calldata.SetUniform3f('lowRanges', low_ranges)
        calldata.SetUniform3f('highRanges', high_ranges)


def win_callback(obj, event):
    global panel, size
    if size != obj.GetSize():
        size_old = size
        size = obj.GetSize()
        size_change = [size[0] - size_old[0], 0]
        panel.re_align(size_change)


if __name__ == '__main__':
    global high_perc, high_ranges, idx_xml, low_perc, low_ranges, \
        panel, scene, size, spheres_actor, xml_files

    xml_files = glob.glob(os.path.join(_DATA_DIR, '*.xml'))

    idx_xml = 0

    centers, colors, radius = read_data()

    scene = window.Scene()

    spheres_actor = actor.billboard(
        centers, colors, scales=radius, fs_dec=_RANGE_CENTERS,
        fs_impl=_FAKE_SPHERE)

    spheres_mapper = spheres_actor.GetMapper()
    spheres_mapper.AddObserver(vtk.vtkCommand.UpdateShaderEvent,
                               vtk_shader_callback)

    scene.add(spheres_actor)

    show_m = window.ShowManager(scene, reset_camera=False,
                                order_transparent=True)
    show_m.initialize()

    panel = ui.Panel2D((480, 270), position=(-185, 5), color=(1, 1, 1),
                       opacity=.1, align='right')

    slider_frame_label = build_label('Frame')
    slider_clipping_plane_label_x = build_label('X Clipping Plane')
    slider_clipping_plane_label_y = build_label('Y Clipping Plane')
    slider_clipping_plane_label_z = build_label('Z Clipping Plane')

    panel.add_element(slider_frame_label, (.04, .85))
    panel.add_element(slider_clipping_plane_label_x, (.04, .55))
    panel.add_element(slider_clipping_plane_label_y, (.04, .35))
    panel.add_element(slider_clipping_plane_label_z, (.04, .15))

    min_centers = np.min(centers, axis=0)
    max_centers = np.max(centers, axis=0)

    low_perc = np.array([50, 50, 50])
    high_perc = np.array([100, 100, 100])

    low_ranges = np.array(
        [np.percentile(centers[:, i], v) for i, v in enumerate(low_perc)]
    )
    high_ranges = np.array(
        [np.percentile(centers[:, i], v) for i, v in enumerate(high_perc)]
    )

    slider_frame_thr = ui.LineSlider2D(
        initial_value=0, min_value=0, max_value=len(xml_files) - 1, length=260,
        line_width=3, outer_radius=8, font_size=16,
        text_template="{value:.0f}")

    slider_clipping_plane_thrs_x = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=8, length=260,
        initial_values=(low_ranges[0], high_ranges[0]),
        min_value=min_centers[0], max_value=max_centers[0], font_size=16,
        text_template="{value:.0f}")

    slider_clipping_plane_thrs_y = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=8, length=260,
        initial_values=(low_ranges[1], high_ranges[1]),
        min_value=min_centers[1], max_value=max_centers[1], font_size=16,
        text_template="{value:.0f}")

    slider_clipping_plane_thrs_z = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=8, length=260,
        initial_values=(low_ranges[2], high_ranges[2]),
        min_value=min_centers[2], max_value=max_centers[2], font_size=16,
        text_template="{value:.0f}")

    slider_frame_thr.on_change = change_frame
    slider_clipping_plane_thrs_x.on_change = change_clipping_plane_x
    slider_clipping_plane_thrs_y.on_change = change_clipping_plane_y
    slider_clipping_plane_thrs_z.on_change = change_clipping_plane_z

    panel.add_element(slider_frame_thr, (.38, .85))
    panel.add_element(slider_clipping_plane_thrs_x, (.38, .55))
    panel.add_element(slider_clipping_plane_thrs_y, (.38, .35))
    panel.add_element(slider_clipping_plane_thrs_z, (.38, .15))

    scene.add(panel)

    size = scene.GetSize()

    show_m.add_window_callback(win_callback)

    show_m.start()
