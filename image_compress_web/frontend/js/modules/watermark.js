import { Utils } from '../utils.js';

/**
 * Watermark Removal Module
 * Logic for single image watermark removal using inpainting (LaMa)
 * Refactored to match H5 style logic
 */

export class WatermarkModule {
    constructor() {
        this.currentFile = null;
        this.originalImage = null;
        this.isDrawing = false;
        this.lastX = 0;
        this.lastY = 0;

        // Initialize
        this.init();
    }

    init() {
        this.bindEvents();
        this.initCanvas();
    }

    // Bind events
    bindEvents() {
        // Single file upload
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('watermarkFileInput');

        if (dropZone && fileInput) {
            dropZone.addEventListener('click', () => fileInput.click());

            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('dragover');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelect(e.target.files[0]);
                }
            });
        }

        // Brush size
        const brushSizeInput = document.getElementById('brushSize');
        if (brushSizeInput) {
            brushSizeInput.addEventListener('input', (e) => {
                document.getElementById('brushSizeValue').textContent = e.target.value;
            });
        }

        // Clear Mask
        const clearBtn = document.getElementById('clearMaskBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearMask());
        }

        // Run Inpainting
        const runBtn = document.getElementById('runInpaintingBtn');
        if (runBtn) {
            runBtn.addEventListener('click', () => this.runInpainting());
        }

        // Save Result
        const saveBtn = document.getElementById('saveResultBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveResult());
        }

        // Reprocess
        const reprocessBtn = document.getElementById('reprocessBtn');
        if (reprocessBtn) {
            reprocessBtn.addEventListener('click', () => this.clearMask());
        }

        // Next Image
        const nextImageBtn = document.getElementById('nextImageBtn');
        if (nextImageBtn) {
            nextImageBtn.addEventListener('click', () => this.reset());
        }
    }

    initCanvas() {
        this.imageCanvas = document.getElementById('imageCanvas');
        this.maskCanvas = document.getElementById('maskCanvas');
        
        if (!this.imageCanvas || !this.maskCanvas) return;

        this.ctxImage = this.imageCanvas.getContext('2d');
        this.ctxMask = this.maskCanvas.getContext('2d');

        // Drawing events
        this.maskCanvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.maskCanvas.addEventListener('mousemove', (e) => this.draw(e));
        this.maskCanvas.addEventListener('mouseup', () => this.stopDrawing());
        this.maskCanvas.addEventListener('mouseleave', () => this.stopDrawing());
        
        // Touch events
        this.maskCanvas.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        this.maskCanvas.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        this.maskCanvas.addEventListener('touchend', () => this.handleTouchEnd());
    }

    // Handle File Selection
    handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            Utils.showToast('请选择图片文件', 'error');
            return;
        }

        this.currentFile = file;

        // Load image
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                this.originalImage = img;
                this.showEditor();
                this.drawImageOnCanvas();
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    showEditor() {
        document.getElementById('singleUploadArea').style.display = 'none';
        document.getElementById('imageEditor').style.display = 'block';
        document.getElementById('watermarkResult').style.display = 'none';
    }

    drawImageOnCanvas() {
        if (!this.originalImage) return;

        // Use natural dimensions for the canvas resolution
        this.imageCanvas.width = this.originalImage.naturalWidth;
        this.imageCanvas.height = this.originalImage.naturalHeight;
        this.maskCanvas.width = this.originalImage.naturalWidth;
        this.maskCanvas.height = this.originalImage.naturalHeight;

        // Draw image at full resolution
        this.ctxImage.clearRect(0, 0, this.imageCanvas.width, this.imageCanvas.height);
        this.ctxImage.drawImage(this.originalImage, 0, 0);

        // Clear mask
        this.clearMask();
    }

    startDrawing(e) {
        e.preventDefault();
        if (!this.originalImage) return;

        this.isDrawing = true;
        const rect = this.maskCanvas.getBoundingClientRect();
        const scaleX = this.maskCanvas.width / rect.width;
        const scaleY = this.maskCanvas.height / rect.height;
        
        this.lastX = (e.clientX - rect.left) * scaleX;
        this.lastY = (e.clientY - rect.top) * scaleY;
    }

    draw(e) {
        if (!this.isDrawing || !this.originalImage) return;
        e.preventDefault();

        const rect = this.maskCanvas.getBoundingClientRect();
        const scaleX = this.maskCanvas.width / rect.width;
        const scaleY = this.maskCanvas.height / rect.height;

        const currentX = (e.clientX - rect.left) * scaleX;
        const currentY = (e.clientY - rect.top) * scaleY;

        this.ctxMask.globalCompositeOperation = 'source-over';
        this.ctxMask.strokeStyle = '#ffcc00'; // Yellow like H5
        
        const baseBrushSize = parseInt(document.getElementById('brushSize').value);
        this.ctxMask.lineWidth = baseBrushSize * scaleX; // Scale brush size
        
        this.ctxMask.lineCap = 'round';
        this.ctxMask.lineJoin = 'round';

        this.ctxMask.beginPath();
        this.ctxMask.moveTo(this.lastX, this.lastY);
        this.ctxMask.lineTo(currentX, currentY);
        this.ctxMask.stroke();

        this.lastX = currentX;
        this.lastY = currentY;
    }

    stopDrawing() {
        this.isDrawing = false;
    }

    handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.maskCanvas.dispatchEvent(mouseEvent);
    }

    handleTouchMove(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.maskCanvas.dispatchEvent(mouseEvent);
    }

    handleTouchEnd() {
        const mouseEvent = new MouseEvent('mouseup', {});
        this.maskCanvas.dispatchEvent(mouseEvent);
    }

    clearMask() {
        this.ctxMask.clearRect(0, 0, this.maskCanvas.width, this.maskCanvas.height);
    }

    async runInpainting() {
        if (!this.originalImage) return;

        // Check for mask
        const maskData = this.ctxMask.getImageData(0, 0, this.maskCanvas.width, this.maskCanvas.height);
        if (!this.hasMaskPixels(maskData)) {
            Utils.showToast('请先涂抹需要去除的水印区域', 'warning');
            return;
        }

        try {
            this.showProgress('正在去除水印...', 30);
            
            // Convert to Blobs (using original resolution)
            const imageBlob = await this.canvasToBlob(this.originalImage);
            const maskBlob = await this.getMaskBlobForProcessing();

            // Prepare API call
            const formData = new FormData();
            formData.append('image', imageBlob, 'image.png');
            formData.append('mask', maskBlob, 'mask.png');
            
            // Add Lama params (matching H5)
            const model = 'lama'; 
            formData.append('ldmSteps', '25');
            formData.append('ldmSampler', 'plms');
            formData.append('zitsWireframe', 'true');
            formData.append('hdStrategy', 'Crop'); 
            formData.append('hdStrategyCropMargin', '196');
            formData.append('hdStrategyCropTrigerSize', '800');
            formData.append('hdStrategyResizeLimit', '2048');
            formData.append('prompt', '');
            formData.append('negativePrompt', '');
            formData.append('croperX', '1109');
            formData.append('croperY', '512');
            formData.append('croperHeight', '512');
            formData.append('croperWidth', '512');
            formData.append('useCroper', 'false');
            formData.append('sdMaskBlur', '5');
            formData.append('sdStrength', '0.75');
            formData.append('sdSteps', '50');
            formData.append('sdGuidanceScale', '7.5');
            formData.append('sdSampler', 'uni_pc');
            formData.append('sdSeed', '-1');
            formData.append('sdMatchHistograms', 'false');
            formData.append('sdScale', '1');
            formData.append('cv2Radius', '5');
            formData.append('cv2Flag', 'INPAINT_NS');
            formData.append('paintByExampleSteps', '50');
            formData.append('paintByExampleGuidanceScale', '7.5');
            formData.append('paintByExampleSeed', '-1');
            formData.append('paintByExampleMaskBlur', '5');
            formData.append('paintByExampleMatchHistograms', 'false');
            formData.append('p2pSteps', '50');
            formData.append('p2pImageGuidanceScale', '1.5');
            formData.append('p2pGuidanceScale', '7.5');
            formData.append('controlnet_conditioning_scale', '0.4');
            formData.append('controlnet_method', 'control_v11p_sd15_canny');

            // Send request
            // Use absolute URL as requested by user
            const response = await fetch('http://127.0.0.1:8080/inpaint', { 
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Processing failed');
            }

            const blob = await response.blob();
            this.showResult(blob);

        } catch (error) {
            Utils.showToast('处理失败: ' + error.message, 'error');
            this.hideProgress();
        }
    }

    hasMaskPixels(imageData) {
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            if (data[i+3] > 0) return true; // Check alpha
        }
        return false;
    }

    canvasToBlob(imageOrCanvas) {
        return new Promise((resolve) => {
            if (imageOrCanvas instanceof HTMLImageElement) {
                const c = document.createElement('canvas');
                c.width = imageOrCanvas.naturalWidth;
                c.height = imageOrCanvas.naturalHeight;
                c.getContext('2d').drawImage(imageOrCanvas, 0, 0);
                c.toBlob(resolve, 'image/png');
            } else {
                imageOrCanvas.toBlob(resolve, 'image/png');
            }
        });
    }

    // Convert drawn mask (on display canvas) to full resolution mask blob
    getMaskBlobForProcessing() {
        const fullMaskCanvas = document.createElement('canvas');
        fullMaskCanvas.width = this.originalImage.naturalWidth;
        fullMaskCanvas.height = this.originalImage.naturalHeight;
        const ctx = fullMaskCanvas.getContext('2d');

        // Draw the mask from the display canvas onto the full resolution canvas
        // scaling it up
        ctx.drawImage(this.maskCanvas, 0, 0, fullMaskCanvas.width, fullMaskCanvas.height);

        // Post-process mask: Convert drawn color (yellow) to white (255,255,255) for the backend
        // Note: The H5 logic checks for yellow pixels and makes them white. 
        // Our draw logic uses alpha. 
        // Simpler approach: Draw the mask canvas onto a black background, treating non-transparent pixels as white.
        
        const finalCanvas = document.createElement('canvas');
        finalCanvas.width = fullMaskCanvas.width;
        finalCanvas.height = fullMaskCanvas.height;
        const finalCtx = finalCanvas.getContext('2d');

        // Fill black
        finalCtx.fillStyle = '#000000';
        finalCtx.fillRect(0, 0, finalCanvas.width, finalCanvas.height);

        // Draw mask in white
        // We use globalCompositeOperation to ensure we only paint where the mask is
        
        // 1. Create a temp canvas with white drawing
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = fullMaskCanvas.width;
        tempCanvas.height = fullMaskCanvas.height;
        const tempCtx = tempCanvas.getContext('2d');
        
        // Draw the scaled mask
        tempCtx.drawImage(this.maskCanvas, 0, 0, tempCanvas.width, tempCanvas.height);
        
        // Replace all non-transparent pixels with white
        const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
        const data = imageData.data;
        for(let i=0; i<data.length; i+=4) {
            if(data[i+3] > 0) { // If alpha > 0
                data[i] = 255;
                data[i+1] = 255;
                data[i+2] = 255;
                data[i+3] = 255;
            }
        }
        tempCtx.putImageData(imageData, 0, 0);

        // Draw white mask onto black background
        finalCtx.drawImage(tempCanvas, 0, 0);

        return new Promise(resolve => finalCanvas.toBlob(resolve, 'image/png'));
    }

    showProgress(text, percent) {
        document.getElementById('watermarkProgress').style.display = 'block';
        document.getElementById('watermarkStatus').textContent = text;
        document.getElementById('watermarkProgressBar').style.width = percent + '%';
    }

    hideProgress() {
        document.getElementById('watermarkProgress').style.display = 'none';
    }

    showResult(blob) {
        this.hideProgress();
        const url = URL.createObjectURL(blob);
        
        // Populate comparison view
        const compareOriginal = document.getElementById('compareOriginal');
        if (this.originalImage) {
            compareOriginal.src = this.originalImage.src;
        }
        
        document.getElementById('processedImage').src = url;
        
        // Don't hide the editor, allowing continuous editing if needed
        // document.getElementById('imageEditor').style.display = 'none'; 
        
        document.getElementById('watermarkResult').style.display = 'block';
        
        // Scroll to result
        document.getElementById('watermarkResult').scrollIntoView({ behavior: 'smooth' });
    }

    saveResult() {
        const img = document.getElementById('processedImage');
        const link = document.createElement('a');
        link.href = img.src;
        link.download = 'watermark_removed_' + (this.currentFile ? this.currentFile.name : 'image.png');
        link.click();
    }

    reset() {
        this.currentFile = null;
        this.originalImage = null;
        document.getElementById('watermarkFileInput').value = '';
        
        document.getElementById('singleUploadArea').style.display = 'block';
        document.getElementById('imageEditor').style.display = 'none';
        document.getElementById('watermarkResult').style.display = 'none';
        
        this.clearMask();
    }
}
