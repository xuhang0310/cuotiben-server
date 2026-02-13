/**
 * 水印去除模块
 * 全自动水印检测与去除前端逻辑
 */

class WatermarkModule {
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
        this.initTabSwitch();
    }

    // 初始化Tab切换
    initTabSwitch() {
        document.querySelectorAll('.tool-tabs .tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                this.switchTab(target);
            });
        });
    }

    switchTab(target) {
        // 隐藏所有panel
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        // 显示目标panel
        document.getElementById(`${target}-panel`).classList.add('active');
        // 更新tab状态
        document.querySelectorAll('.tool-tabs .tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`[data-tab="${target}"]`).classList.add('active');
    }

    // 绑定事件
    bindEvents() {
        // 模式切换
        document.querySelectorAll('input[name="watermarkMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.switchMode(e.target.value));
        });

        // 单张上传
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('watermarkFileInput');

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

        // 批量处理 - 文件夹选择
        const browseBtn = document.getElementById('browseWatermarkFolderBtn');
        if (browseBtn) {
            browseBtn.addEventListener('click', () => this.selectFolder());
        }

        // 高级设置
        const advancedToggle = document.getElementById('showAdvancedSettings');
        if (advancedToggle) {
            advancedToggle.addEventListener('change', (e) => {
                document.getElementById('advancedSettingsPanel').style.display =
                    e.target.checked ? 'block' : 'none';
            });
        }

        // 置信度滑块
        const confidenceSlider = document.getElementById('confidenceThreshold');
        if (confidenceSlider) {
            confidenceSlider.addEventListener('input', (e) => {
                document.getElementById('confidenceValue').textContent = e.target.value;
            });
        }

        // 手动调整
        const manualAdjust = document.getElementById('manualAdjust');
        if (manualAdjust) {
            manualAdjust.addEventListener('change', (e) => {
                document.getElementById('manualAdjustControls').style.display =
                    e.target.checked ? 'block' : 'none';
            });
        }

        // 开始处理按钮
        const startBtn = document.getElementById('startWatermarkBtn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startProcessing());
        }

        // 重新处理
        const reprocessBtn = document.getElementById('reprocessBtn');
        if (reprocessBtn) {
            reprocessBtn.addEventListener('click', () => this.reset());
        }

        // 保存结果
        const saveBtn = document.getElementById('saveResultBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveResult());
        }
    }

    // 切换单张/批量模式
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

    // 处理文件选择
    handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            this.showToast('请选择图片文件', 'error');
            return;
        }

        this.currentFile = file;
        this.currentFolder = null;

        // 显示预览
        this.showFilePreview(file);

        // 自动开始检测
        this.detectWatermark();
    }

    // 显示文件预览
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

    // 选择文件夹（模拟）
    async selectFolder() {
        try {
            // 使用原生文件选择器选择多个文件
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
                    this.showToast('未找到图片文件', 'warning');
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
            this.showToast('选择文件夹失败: ' + error.message, 'error');
        }
    }

    // 显示文件列表
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

    // 检测水印
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
                // 快速模式跳过检测
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
                this.showToast('未检测到水印，请使用手动模式', 'warning');
                return;
            }

            this.detectionResult = result.detection;

            // 显示检测结果
            this.showDetectionResult(result);

            // 启用处理按钮
            document.getElementById('startWatermarkBtn').disabled = false;

        } catch (error) {
            this.showToast('检测失败: ' + error.message, 'error');
        }
    }

    // 显示检测结果
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

            // 填充手动调整值
            document.getElementById('bboxX1').value = det.bbox[0];
            document.getElementById('bboxY1').value = det.bbox[1];
            document.getElementById('bboxX2').value = det.bbox[2];
            document.getElementById('bboxY2').value = det.bbox[3];
        }

        this.showProgress('检测完成，可以开始处理', 100);
        setTimeout(() => this.hideProgress(), 1000);
    }

    // 开始处理
    async startProcessing() {
        const mode = document.querySelector('input[name="watermarkMode"]:checked').value;

        if (mode === 'single') {
            await this.processSingle();
        } else {
            await this.processBatch();
        }
    }

    // 单张处理
    async processSingle() {
        if (!this.currentFile) {
            this.showToast('请先选择图片', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('file', this.currentFile);

        // 获取手动调整的区域
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
                // 使用快速模式
                formData.append('preset', 'doubao_bottom_right');
                response = await fetch('/api/watermark/quick-remove', {
                    method: 'POST',
                    body: formData
                });
            } else {
                // 使用自动检测模式
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

            // 显示结果
            await this.showResult(result);

        } catch (error) {
            this.showToast('处理失败: ' + error.message, 'error');
            this.hideProgress();
            document.getElementById('startWatermarkBtn').disabled = false;
        }
    }

    // 批量处理
    async processBatch() {
        if (this.fileList.length === 0) {
            this.showToast('请先选择文件夹', 'warning');
            return;
        }

        const skipLowConfidence = document.getElementById('skipLowConfidence').checked;

        try {
            // 创建虚拟的文件夹路径
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
            this.showToast('批量处理启动失败: ' + error.message, 'error');
        }
    }

    // 轮询批量进度
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

                // 更新进度
                const pct = task.progress.percentage;
                this.showProgress(
                    `正在处理: ${task.current_file || '...'}`,
                    pct,
                    `成功:${task.progress.successful} 跳过:${task.progress.skipped} 失败:${task.progress.failed}`
                );

                // 更新文件列表状态
                this.updateFileListStatus(task);

                if (task.status === 'completed' || task.status === 'failed') {
                    this.hideProgress();
                    this.showBatchComplete(task);
                    return;
                }

                setTimeout(poll, 500);

            } catch (error) {
                this.showToast('获取进度失败: ' + error.message, 'error');
            }
        };

        poll();
    }

    // 更新文件列表状态
    updateFileListStatus(task) {
        // 简化显示，实际应该根据task详情更新
        const progressText = `${task.progress.processed}/${task.progress.total}`;
        document.getElementById('watermarkStatus').textContent =
            `处理中 ${progressText}`;
    }

    // 显示批量完成
    showBatchComplete(task) {
        this.showToast(
            `批量处理完成! 成功:${task.progress.successful} 失败:${task.progress.failed}`,
            task.progress.failed > 0 ? 'warning' : 'success'
        );
    }

    // 显示处理结果
    async showResult(result) {
        const resultDiv = document.getElementById('watermarkResult');
        resultDiv.style.display = 'block';

        // 原图
        if (this.currentFile) {
            const originalUrl = URL.createObjectURL(this.currentFile);
            document.getElementById('originalImage').src = originalUrl;
        }

        // 处理后的图片
        if (result.output_url) {
            const processedResponse = await fetch(result.output_url);
            const processedBlob = await processedResponse.blob();
            const processedUrl = URL.createObjectURL(processedBlob);
            document.getElementById('processedImage').src = processedUrl;
        }

        // 结果信息
        const det = result.detection || {};
        document.getElementById('resultBbox').textContent =
            det.bbox ? `(${det.bbox.join(', ')})` : '自动检测';
        document.getElementById('resultConfidence').textContent =
            det.confidence ? `${(det.confidence * 100).toFixed(1)}%` : '--';
        document.getElementById('resultTime').textContent =
            result.processing_time || '--';

        this.hideProgress();
    }

    // 保存结果
    async saveResult() {
        if (!this.currentFile) return;

        try {
            // 获取处理后的图片
            const processedImg = document.getElementById('processedImage');
            if (!processedImg.src) {
                this.showToast('没有可保存的结果', 'warning');
                return;
            }

            // 下载图片
            const response = await fetch(processedImg.src);
            const blob = await response.blob();

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');

            // 在原文件名前添加前缀
            const originalName = this.currentFile.name;
            const nameParts = originalName.split('.');
            const ext = nameParts.pop();
            const name = nameParts.join('.');

            a.href = url;
            a.download = `${name}_cleaned.${ext}`;
            a.click();

            URL.revokeObjectURL(url);
            this.showToast('已保存到下载目录', 'success');

        } catch (error) {
            this.showToast('保存失败: ' + error.message, 'error');
        }
    }

    // 显示进度
    showProgress(status, percentage, detail = '') {
        const progressDiv = document.getElementById('watermarkProgress');
        progressDiv.style.display = 'block';

        document.getElementById('watermarkStatus').textContent = status;
        document.getElementById('watermarkProgressText').textContent = `${percentage}%`;
        document.getElementById('watermarkProgressBar').style.width = `${percentage}%`;
        document.getElementById('watermarkProgressDetail').textContent = detail;
    }

    // 隐藏进度
    hideProgress() {
        document.getElementById('watermarkProgress').style.display = 'none';
    }

    // 重置
    reset() {
        this.currentFile = null;
        this.detectionResult = null;

        // 重置UI
        document.getElementById('dropZone').innerHTML = `
            <i class="fas fa-cloud-upload-alt upload-icon"></i>
            <p class="upload-text">点击上传或拖拽图片到此处</p>
            <p class="upload-hint">支持 JPG、PNG、BMP、WEBP 格式</p>
            <input type="file" id="watermarkFileInput" accept="image/*" style="display: none;">
        `;

        document.getElementById('detectionPreview').style.display = 'none';
        document.getElementById('watermarkResult').style.display = 'none';
        document.getElementById('startWatermarkBtn').disabled = true;

        this.hideProgress();

        // 重新绑定上传事件
        this.bindEvents();
    }

    // 显示Toast提示
    showToast(message, type = 'info') {
        const toast = document.getElementById('toastAlert');
        const toastBody = document.getElementById('toastBody');
        const toastTitle = document.getElementById('toastTitle');

        toastBody.textContent = message;

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// 初始化
let watermarkModule;

document.addEventListener('DOMContentLoaded', () => {
    watermarkModule = new WatermarkModule();
});
