import { Utils } from '../utils.js';

/**
 * Watermark Removal Module
 * Logic for automated watermark detection and removal
 */

export class WatermarkModule {
    constructor() {
        this.currentFile = null;
        this.currentFolder = null;
        this.fileList = [];
        this.detectionResult = null;
        this.taskId = null;

        this.init();
    }

    init() {
        this.bindEvents();
    }

    // Bind events
    bindEvents() {
        // Mode switch
        document.querySelectorAll('input[name="watermarkMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.switchMode(e.target.value));
        });

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

        // Batch processing - Folder selection
        const browseBtn = document.getElementById('browseWatermarkFolderBtn');
        if (browseBtn) {
            browseBtn.addEventListener('click', () => this.selectFolder());
        }

        // Advanced Settings
        const advancedToggle = document.getElementById('showAdvancedSettings');
        if (advancedToggle) {
            advancedToggle.addEventListener('change', (e) => {
                document.getElementById('advancedSettingsPanel').style.display =
                    e.target.checked ? 'block' : 'none';
            });
        }

        // Confidence Slider
        const confidenceSlider = document.getElementById('confidenceThreshold');
        if (confidenceSlider) {
            confidenceSlider.addEventListener('input', (e) => {
                document.getElementById('confidenceValue').textContent = e.target.value;
            });
        }

        // Manual Adjust
        const manualAdjust = document.getElementById('manualAdjust');
        if (manualAdjust) {
            manualAdjust.addEventListener('change', (e) => {
                document.getElementById('manualAdjustControls').style.display =
                    e.target.checked ? 'block' : 'none';
            });
        }

        // Start Processing Button
        const startBtn = document.getElementById('startWatermarkBtn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startProcessing());
        }

        // Reprocess
        const reprocessBtn = document.getElementById('reprocessBtn');
        if (reprocessBtn) {
            reprocessBtn.addEventListener('click', () => this.reset());
        }

        // Save Result
        const saveBtn = document.getElementById('saveResultBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveResult());
        }
    }

    // Switch Single/Batch Mode
    switchMode(mode) {
        const singleArea = document.getElementById('singleUploadArea');
        const batchArea = document.getElementById('batchUploadArea');

        if (mode === 'single') {
            singleArea.style.display = 'block';
            batchArea.style.display = 'none';
        } else {
            singleArea.style.display = 'none';
            batchArea.style.display = 'block';
        }

        this.reset();
    }

    // Handle File Selection
    handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            Utils.showToast('请选择图片文件', 'error');
            return;
        }

        this.currentFile = file;
        this.currentFolder = null;

        // Show Preview
        this.showFilePreview(file);

        // Auto start detection
        this.detectWatermark();
    }

    // Show File Preview
    showFilePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const dropZone = document.getElementById('dropZone');
            dropZone.innerHTML = `
                <img src="${e.target.result}" style="max-height: 200px; max-width: 100%; border-radius: 8px;">
                <p class="mt-2 mb-0">${file.name}</p>
                <p class="text-muted small">点击更换图片</p>
            `;
        };
        reader.readAsDataURL(file);
    }

    // Select Folder (Mock)
    async selectFolder() {
        try {
            // Use native file picker to select multiple files
            const input = document.createElement('input');
            input.type = 'file';
            input.webkitdirectory = true;
            input.directory = true;
            input.multiple = true;

            input.onchange = (e) => {
                const files = Array.from(e.target.files).filter(f =>
                    f.type.startsWith('image/')
                );

                if (files.length === 0) {
                    Utils.showToast('未找到图片文件', 'warning');
                    return;
                }

                this.fileList = files;
                this.currentFolder = files[0].path || files[0].name;

                document.getElementById('watermarkFolderPath').value =
                    `已选择 ${files.length} 张图片`;

                this.showFileList(files);
                document.getElementById('startWatermarkBtn').disabled = false;
            };

            input.click();
        } catch (error) {
            Utils.showToast('选择文件夹失败: ' + error.message, 'error');
        }
    }

    // Show File List
    showFileList(files) {
        const container = document.getElementById('watermarkFileList');
        container.innerHTML = files.map((file, index) => `
            <div class="file-item" data-index="${index}">
                <i class="fas fa-image file-icon"></i>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-status pending" id="status-${index}">等待处理</div>
                </div>
            </div>
        `).join('');
    }

    // Detect Watermark
    async detectWatermark() {
        if (!this.currentFile) return;

        const formData = new FormData();
        formData.append('file', this.currentFile);
        formData.append('visualize', 'true');

        const mode = document.getElementById('detectionMode').value;

        try {
            this.showProgress('正在检测水印位置...', 10);

            let result;
            if (mode === 'quick') {
                // Quick mode skips detection
                result = {
                    success: true,
                    detection: {
                        bbox: null,
                        confidence: 0.85,
                        mode: 'normal'
                    }
                };
            } else {
                const response = await fetch('/api/watermark/detect-only', {
                    method: 'POST',
                    body: formData
                });
                result = await response.json();
            }

            if (!result.success) {
                Utils.showToast('未检测到水印，请使用手动模式', 'warning');
                return;
            }

            this.detectionResult = result.detection;

            // Show detection result
            this.showDetectionResult(result);

            // Enable process button
            document.getElementById('startWatermarkBtn').disabled = false;

        } catch (error) {
            Utils.showToast('检测失败: ' + error.message, 'error');
        }
    }

    // Show Detection Result
    showDetectionResult(result) {
        const preview = document.getElementById('detectionPreview');
        preview.style.display = 'block';

        if (result.visualization_url) {
            document.getElementById('detectionPreviewImg').src = result.visualization_url;
        }

        const det = result.detection || result;
        document.getElementById('detectionConfidence').textContent =
            `置信度: ${(det.confidence * 100).toFixed(1)}%`;

        if (det.bbox) {
            document.getElementById('detectionRegion').textContent =
                `区域: (${det.bbox.join(', ')})`;

            // Fill manual adjust values
            document.getElementById('bboxX1').value = det.bbox[0];
            document.getElementById('bboxY1').value = det.bbox[1];
            document.getElementById('bboxX2').value = det.bbox[2];
            document.getElementById('bboxY2').value = det.bbox[3];
        }

        this.showProgress('检测完成，可以开始处理', 100);
        setTimeout(() => this.hideProgress(), 1000);
    }

    // Start Processing
    async startProcessing() {
        const mode = document.querySelector('input[name="watermarkMode"]:checked').value;

        if (mode === 'single') {
            await this.processSingle();
        } else {
            await this.processBatch();
        }
    }

    // Process Single File
    async processSingle() {
        if (!this.currentFile) {
            Utils.showToast('请先选择图片', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('file', this.currentFile);

        // Get manual adjust region
        const manualAdjust = document.getElementById('manualAdjust').checked;
        if (manualAdjust) {
            const bbox = [
                parseInt(document.getElementById('bboxX1').value),
                parseInt(document.getElementById('bboxY1').value),
                parseInt(document.getElementById('bboxX2').value),
                parseInt(document.getElementById('bboxY2').value)
            ];
            formData.append('bbox', JSON.stringify(bbox));
        }

        const detectionMode = document.getElementById('detectionMode').value;

        try {
            this.showProgress('正在去除水印...', 30);
            document.getElementById('startWatermarkBtn').disabled = true;

            let response;
            if (detectionMode === 'quick') {
                // Use quick mode
                formData.append('preset', 'doubao_bottom_right');
                response = await fetch('/api/watermark/quick-remove', {
                    method: 'POST',
                    body: formData
                });
            } else {
                // Use auto detection mode
                const confidence = document.getElementById('confidenceThreshold').value;
                formData.append('min_confidence', confidence);
                formData.append('visualize', 'true');

                response = await fetch('/api/watermark/auto-remove', {
                    method: 'POST',
                    body: formData
                });
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || '处理失败');
            }

            this.showProgress('处理完成！', 100);

            // Show result
            await this.showResult(result);

        } catch (error) {
            Utils.showToast('处理失败: ' + error.message, 'error');
            this.hideProgress();
            document.getElementById('startWatermarkBtn').disabled = false;
        }
    }

    // Process Batch
    async processBatch() {
        if (this.fileList.length === 0) {
            Utils.showToast('请先选择文件夹', 'warning');
            return;
        }

        const skipLowConfidence = document.getElementById('skipLowConfidence').checked;

        try {
            // Create virtual folder paths
            const inputFolder = '/tmp/watermark_batch_input';
            const outputFolder = '/tmp/watermark_batch_output';

            const response = await fetch('/api/watermark/batch-remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    input_folder: inputFolder,
                    output_folder: outputFolder,
                    skip_low_confidence: skipLowConfidence
                })
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || '启动失败');
            }

            this.taskId = result.task_id;
            this.pollBatchProgress();

        } catch (error) {
            Utils.showToast('批量处理启动失败: ' + error.message, 'error');
        }
    }

    // Poll Batch Progress
    async pollBatchProgress() {
        if (!this.taskId) return;

        const poll = async () => {
            try {
                const response = await fetch(`/api/watermark/task/${this.taskId}`);
                const result = await response.json();

                if (!result.success) {
                    throw new Error('获取进度失败');
                }

                const task = result.task;

                // Update progress
                const pct = task.progress.percentage;
                this.showProgress(
                    `正在处理: ${task.current_file || '...'}`,
                    pct,
                    `成功:${task.progress.successful} 跳过:${task.progress.skipped} 失败:${task.progress.failed}`
                );

                // Update file list status
                this.updateFileListStatus(task);

                if (task.status === 'completed' || task.status === 'failed') {
                    this.hideProgress();
                    this.showBatchComplete(task);
                    return;
                }

                setTimeout(poll, 500);

            } catch (error) {
                Utils.showToast('获取进度失败: ' + error.message, 'error');
            }
        };

        poll();
    }

    // Update File List Status
    updateFileListStatus(task) {
        // Simplified display, should actually update based on task details
        const progressText = `${task.progress.processed}/${task.progress.total}`;
        document.getElementById('watermarkStatus').textContent =
            `处理中 ${progressText}`;
    }

    // Show Batch Complete
    showBatchComplete(task) {
        Utils.showToast(
            `批量处理完成! 成功:${task.progress.successful} 失败:${task.progress.failed}`,
            task.progress.failed > 0 ? 'warning' : 'success'
        );
    }

    // Show Result
    async showResult(result) {
        const resultDiv = document.getElementById('watermarkResult');
        resultDiv.style.display = 'block';

        // Original Image
        if (this.currentFile) {
            const originalUrl = URL.createObjectURL(this.currentFile);
            document.getElementById('originalImage').src = originalUrl;
        }

        // Processed Image
        if (result.output_url) {
            const processedResponse = await fetch(result.output_url);
            const processedBlob = await processedResponse.blob();
            const processedUrl = URL.createObjectURL(processedBlob);
            document.getElementById('processedImage').src = processedUrl;
        }

        // Result Info
        const det = result.detection || {};
        document.getElementById('resultBbox').textContent =
            det.bbox ? `(${det.bbox.join(', ')})` : '自动检测';
        document.getElementById('resultConfidence').textContent =
            det.confidence ? `${(det.confidence * 100).toFixed(1)}%` : '--';
        document.getElementById('resultTime').textContent =
            result.processing_time || '--';

        this.hideProgress();
    }

    // Save Result
    async saveResult() {
        if (!this.currentFile) return;

        try {
            // Get processed image
            const processedImg = document.getElementById('processedImage');
            if (!processedImg.src) {
                Utils.showToast('没有可保存的结果', 'warning');
                return;
            }

            // Download image
            const response = await fetch(processedImg.src);
            const blob = await response.blob();

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');

            // Add prefix to original filename
            const originalName = this.currentFile.name;
            const nameParts = originalName.split('.');
            const ext = nameParts.pop();
            const name = nameParts.join('.');

            a.href = url;
            a.download = `${name}_cleaned.${ext}`;
            a.click();

            URL.revokeObjectURL(url);
            Utils.showToast('已保存到下载目录', 'success');

        } catch (error) {
            Utils.showToast('保存失败: ' + error.message, 'error');
        }
    }

    // Show Progress
    showProgress(status, percentage, detail = '') {
        const progressDiv = document.getElementById('watermarkProgress');
        progressDiv.style.display = 'block';

        document.getElementById('watermarkStatus').textContent = status;
        document.getElementById('watermarkProgressText').textContent = `${percentage}%`;
        document.getElementById('watermarkProgressBar').style.width = `${percentage}%`;
        document.getElementById('watermarkProgressDetail').textContent = detail;
    }

    // Hide Progress
    hideProgress() {
        document.getElementById('watermarkProgress').style.display = 'none';
    }

    // Reset
    reset() {
        this.currentFile = null;
        this.detectionResult = null;

        // Reset UI
        document.getElementById('dropZone').innerHTML = `
            <i class="fas fa-cloud-upload-alt upload-icon"></i>
            <p class="upload-text">点击上传或拖拽图片到此处</p>
            <p class="upload-hint">支持 JPG、PNG、BMP、WEBP 格式</p>
        `;
        
        // Reset file input
        const fileInput = document.getElementById('watermarkFileInput');
        if (fileInput) {
            fileInput.value = '';
        }

        document.getElementById('detectionPreview').style.display = 'none';
        document.getElementById('watermarkResult').style.display = 'none';
        document.getElementById('startWatermarkBtn').disabled = true;

        this.hideProgress();
    }
}
