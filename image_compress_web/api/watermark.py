import cv2
import numpy as np
import torch
import random
import time
import logging
from PIL import Image
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response

from watermark.lama.schema import Config
from watermark.lama.helper import load_img, pil_to_bytes
from .deps import get_lama_model_manager, get_watermark_remover

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/watermark/auto-remove")
async def watermark_auto_remove(
    file: UploadFile = File(...),
    min_confidence: float = Form(0.5),
    visualize: bool = Form(False)
):
    """
    全自动检测并去除水印
    """
    import uuid
    temp_id = uuid.uuid4().hex[:12]
    input_path = f"/tmp/watermark_input_{temp_id}.jpg"
    output_path = f"/tmp/watermark_output_{temp_id}.jpg"
    vis_path = f"/tmp/watermark_vis_{temp_id}.jpg" if visualize else None

    try:
        # 保存上传的文件
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 获取去除器实例
        watermark_remover = get_watermark_remover()

        # 执行去除
        result = watermark_remover.remove(
            input_path,
            output_path,
            min_confidence=min_confidence,
            visualize=visualize,
            visualization_path=vis_path
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Processing failed'))

        response = {
            "success": True,
            "detection": result['detection'],
            "processing_time": result['processing_time'],
            "output_url": f"/api/watermark/download/{temp_id}"
        }
        return response
    except Exception as e:
        logger.error(f"Auto remove error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup can be done here or via background task
        pass

@router.post("/inpaint")
async def inpaint_process(
    image: UploadFile = File(...),
    mask: UploadFile = File(...),
    ldmSteps: int = Form(25),
    ldmSampler: str = Form("plms"),
    hdStrategy: str = Form("Original"),
    zitsWireframe: bool = Form(True),
    hdStrategyCropMargin: int = Form(128),
    hdStrategyCropTrigerSize: int = Form(2048),
    hdStrategyResizeLimit: int = Form(2048),
    prompt: str = Form(""),
    negativePrompt: str = Form(""),
    useCroper: bool = Form(False),
    croperX: int = Form(0),
    croperY: int = Form(0),
    croperHeight: int = Form(512),
    croperWidth: int = Form(512),
    sdScale: float = Form(1.0),
    sdMaskBlur: int = Form(5),
    sdStrength: float = Form(0.75),
    sdSteps: int = Form(50),
    sdGuidanceScale: float = Form(7.5),
    sdSampler: str = Form("uni_pc"),
    sdSeed: int = Form(-1),
    sdMatchHistograms: bool = Form(False),
    cv2Flag: str = Form("INPAINT_NS"),
    cv2Radius: int = Form(5),
    paintByExampleSteps: int = Form(50),
    paintByExampleGuidanceScale: float = Form(7.5),
    paintByExampleMaskBlur: int = Form(5),
    paintByExampleSeed: int = Form(-1),
    paintByExampleMatchHistograms: bool = Form(False),
    p2pSteps: int = Form(50),
    p2pImageGuidanceScale: float = Form(1.5),
    p2pGuidanceScale: float = Form(7.5),
    controlnet_conditioning_scale: float = Form(0.4),
    controlnet_method: str = Form("control_v11p_sd15_canny"),
    paintByExampleImage: UploadFile = File(None)
):
    """
    Inpainting API based on Lama Cleaner logic
    """
    model_manager = get_lama_model_manager()
    
    # Read image
    origin_image_bytes = await image.read()
    image_np, alpha_channel, exif = load_img(origin_image_bytes, return_exif=True)
    
    # Read mask
    mask_bytes = await mask.read()
    mask_np, _ = load_img(mask_bytes, gray=True)
    mask_np = cv2.threshold(mask_np, 127, 255, cv2.THRESH_BINARY)[1]
    
    if image_np.shape[:2] != mask_np.shape[:2]:
        # Try to resize mask to match image
        # This can happen if canvas size differs slightly from image due to rounding or scaling
        # But we should trust the image size
        logger.warning(f"Mask shape {mask_np.shape[:2]} mismatch Image shape {image_np.shape[:2]}. Resizing mask.")
        mask_np = cv2.resize(mask_np, (image_np.shape[1], image_np.shape[0]), interpolation=cv2.INTER_NEAREST)

    original_shape = image_np.shape
    
    # Handle Paint By Example
    pbe_image = None
    if paintByExampleImage:
        pbe_bytes = await paintByExampleImage.read()
        pbe_np, _ = load_img(pbe_bytes)
        pbe_image = Image.fromarray(pbe_np)

    # Config
    config = Config(
        ldm_steps=ldmSteps,
        ldm_sampler=ldmSampler,
        hd_strategy=hdStrategy,
        zits_wireframe=zitsWireframe,
        hd_strategy_crop_margin=hdStrategyCropMargin,
        hd_strategy_crop_trigger_size=hdStrategyCropTrigerSize,
        hd_strategy_resize_limit=hdStrategyResizeLimit,
        prompt=prompt,
        negative_prompt=negativePrompt,
        use_croper=useCroper,
        croper_x=croperX,
        croper_y=croperY,
        croper_height=croperHeight,
        croper_width=croperWidth,
        sd_scale=sdScale,
        sd_mask_blur=sdMaskBlur,
        sd_strength=sdStrength,
        sd_steps=sdSteps,
        sd_guidance_scale=sdGuidanceScale,
        sd_sampler=sdSampler,
        sd_seed=sdSeed,
        sd_match_histograms=sdMatchHistograms,
        cv2_flag=cv2Flag,
        cv2_radius=cv2Radius,
        paint_by_example_steps=paintByExampleSteps,
        paint_by_example_guidance_scale=paintByExampleGuidanceScale,
        paint_by_example_mask_blur=paintByExampleMaskBlur,
        paint_by_example_seed=paintByExampleSeed,
        paint_by_example_match_histograms=paintByExampleMatchHistograms,
        paint_by_example_example_image=pbe_image,
        p2p_steps=p2pSteps,
        p2p_image_guidance_scale=p2pImageGuidanceScale,
        p2p_guidance_scale=p2pGuidanceScale,
        controlnet_conditioning_scale=controlnet_conditioning_scale,
    )

    if config.sd_seed == -1:
        config.sd_seed = random.randint(1, 999999999)
    if config.paint_by_example_seed == -1:
        config.paint_by_example_seed = random.randint(1, 999999999)

    logger.info(f"Origin image shape: {original_shape}")
    
    start = time.time()
    try:
        res_np_img = model_manager(image_np, mask_np, config)
    except RuntimeError as e:
        torch.cuda.empty_cache()
        if "CUDA out of memory" in str(e):
            raise HTTPException(status_code=500, detail="CUDA out of memory")
        else:
            logger.exception(e)
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        logger.info(f"process time: {(time.time() - start) * 1000}ms")
        torch.cuda.empty_cache()

    # Post processing
    res_np_img = cv2.cvtColor(res_np_img.astype(np.uint8), cv2.COLOR_BGR2RGB)
    if alpha_channel is not None:
        if alpha_channel.shape[:2] != res_np_img.shape[:2]:
            alpha_channel = cv2.resize(
                alpha_channel, dsize=(res_np_img.shape[1], res_np_img.shape[0])
            )
        res_np_img = np.concatenate(
            (res_np_img, alpha_channel[:, :, np.newaxis]), axis=-1
        )

    ext = "png" # Default to png for high quality result
    
    if exif is not None:
        image_bytes = pil_to_bytes(Image.fromarray(res_np_img), ext, quality=95, exif=exif)
    else:
        image_bytes = pil_to_bytes(Image.fromarray(res_np_img), ext, quality=95)

    return Response(content=image_bytes, media_type=f"image/{ext}")
