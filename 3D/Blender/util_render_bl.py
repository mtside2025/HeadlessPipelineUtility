import bpy
import json

# setting of renderer
def setRenderParameter(
    scene,
    json_file_name="default"
    ):
    
    with open(f"render/{json_file_name}.json") as f:
        render_setting = json.load(f)
    
    scene.render.resolution_x = render_setting["resolution_x"]
    scene.render.resolution_y = render_setting["resolution_y"]
    scene.render.resolution_percentage = render_setting["resolution_percentage"]
    
    scene.render.engine = "CYCLES"
    scene.cycles.samples = render_setting["render_samples"] # sample count of ray-tracing results
    scene.cycles.use_denoising = render_setting["use_denoising"]
    
    # GPU enable
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
    scene.cycles.device = 'GPU'
    
    
    # FFMPEG settins
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = render_setting["bitrate_types"][render_setting["selected_bitrate_type_index"]] # HIGH/MEDIUM/LOW/NONE(CBR)
    scene.render.ffmpeg.gopsize = render_setting["gop_size"]
    
    # sampling-rate settins
    scene.render.fps = render_setting["frame_rate"]
    
    # timeline start and end settings
    bpy.context.scene.frame_end = 1500
    
    return render_setting

