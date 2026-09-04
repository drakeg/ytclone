(() => {
    const videoInput = document.getElementById('id_video_file');
    const thumbnailInput = document.getElementById('id_thumbnail');
    const frameInput = document.getElementById('id_thumbnail_frame_seconds');
    const modeInputs = Array.from(document.querySelectorAll('input[name="thumbnail_mode"]'));
    if (!videoInput || !thumbnailInput || !frameInput || !modeInputs.length) return;

    const modeContainer = modeInputs[0].closest('p') || modeInputs[0].parentElement;
    const thumbnailContainer = thumbnailInput.closest('p') || thumbnailInput.parentElement;
    if (!modeContainer || !thumbnailContainer) return;

    const picker = document.createElement('section');
    picker.id = 'thumbnail-frame-picker';
    picker.className = 'card mb-3';
    picker.hidden = true;
    picker.innerHTML = `
        <div class="card-body">
            <h2 class="h5">Choose a frame from your video</h2>
            <p class="video-meta">Use the video controls to find the exact frame you want, then save the current frame.</p>
            <video id="thumbnail-video-preview" class="w-100 mb-3" controls preload="metadata" style="max-height: 420px;"></video>
            <div class="d-flex gap-2 align-items-center flex-wrap">
                <button id="thumbnail-use-frame" type="button" class="btn btn-outline-primary">Use current frame</button>
                <span id="thumbnail-frame-status" class="helptext" aria-live="polite">No frame selected yet.</span>
            </div>
        </div>`;
    modeContainer.insertAdjacentElement('afterend', picker);

    const preview = document.getElementById('thumbnail-video-preview');
    const useFrameButton = document.getElementById('thumbnail-use-frame');
    const frameStatus = document.getElementById('thumbnail-frame-status');
    let objectUrl = null;

    const selectedMode = () => {
        const selected = modeInputs.find((input) => input.checked);
        return selected ? selected.value : 'auto';
    };

    const formatTime = (seconds) => {
        const whole = Math.max(0, Math.floor(seconds));
        const hours = Math.floor(whole / 3600);
        const minutes = Math.floor((whole % 3600) / 60);
        const secs = whole % 60;
        if (hours) return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        return `${minutes}:${String(secs).padStart(2, '0')}`;
    };

    const refreshVideoPreview = () => {
        if (objectUrl) {
            URL.revokeObjectURL(objectUrl);
            objectUrl = null;
        }
        const file = videoInput.files && videoInput.files[0];
        if (!file) {
            preview.removeAttribute('src');
            preview.load();
            return;
        }
        objectUrl = URL.createObjectURL(file);
        preview.src = objectUrl;
    };

    const refreshMode = () => {
        const mode = selectedMode();
        picker.hidden = mode !== 'frame';
        thumbnailContainer.hidden = mode !== 'custom';
        thumbnailInput.required = mode === 'custom';
        if (mode !== 'frame') {
            frameInput.value = '';
            frameStatus.textContent = 'No frame selected yet.';
        }
        if (mode === 'frame' && !preview.src) refreshVideoPreview();
    };

    modeInputs.forEach((input) => input.addEventListener('change', refreshMode));
    videoInput.addEventListener('change', () => {
        frameInput.value = '';
        frameStatus.textContent = 'No frame selected yet.';
        refreshVideoPreview();
    });
    useFrameButton.addEventListener('click', () => {
        if (!preview.src || !Number.isFinite(preview.currentTime)) {
            frameStatus.textContent = 'Select a video first.';
            return;
        }
        frameInput.value = preview.currentTime.toFixed(3);
        frameStatus.textContent = `Selected ${formatTime(preview.currentTime)}.`;
    });
    window.addEventListener('beforeunload', () => {
        if (objectUrl) URL.revokeObjectURL(objectUrl);
    });

    refreshVideoPreview();
    refreshMode();
})();
