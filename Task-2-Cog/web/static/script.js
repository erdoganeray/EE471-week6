// Cat-kind classifier page: choose/drop a photo, send it to /api/classify, show the result.

const BREED_NAMES = {
    "tabby": "Tabby",
    "tiger cat": "Tiger cat",
    "Persian cat": "Persian",
    "Siamese cat": "Siamese",
    "Egyptian cat": "Egyptian Mau",
};

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const preview = document.getElementById("preview");
const dropzoneText = document.getElementById("dropzone-text");
const classifyButton = document.getElementById("classify-button");
const errorBox = document.getElementById("error");
const result = document.getElementById("result");
const modelStatus = document.getElementById("model-status");
const modelStatusText = document.getElementById("model-status-text");

let selectedFile = null;

function percent(value) {
    return `${(value * 100).toFixed(1)}%`;
}

function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = !message;
}

function selectFile(file) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
        showError("Please choose an image file.");
        return;
    }
    selectedFile = file;
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
    dropzoneText.hidden = true;
    classifyButton.disabled = false;
    result.hidden = true;
    showError("");
}

fileInput.addEventListener("change", () => selectFile(fileInput.files[0]));

dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("dragging");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragging"));
dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragging");
    selectFile(event.dataTransfer.files[0]);
});

function renderBars(title, items, labelOf) {
    document.getElementById("bars-title").textContent = title;
    const bars = document.getElementById("bars");
    bars.replaceChildren();
    items.forEach((item, index) => {
        const row = document.createElement("li");
        if (index === 0) row.className = "best";

        const label = document.createElement("span");
        label.textContent = labelOf(item.label);
        const track = document.createElement("span");
        track.className = "track";
        const fill = document.createElement("span");
        fill.className = "fill";
        fill.style.width = percent(item.probability);
        track.append(fill);
        const value = document.createElement("span");
        value.className = "value";
        value.textContent = percent(item.probability);

        row.append(label, track, value);
        bars.append(row);
    });
}

function renderResult(output) {
    const title = document.getElementById("result-title");
    const detail = document.getElementById("result-detail");

    if (output.is_cat) {
        title.textContent = `${BREED_NAMES[output.breed] ?? output.breed} · ${percent(output.confidence)}`;
        detail.textContent = `The model is ${percent(output.cat_score)} sure this is a cat.`;
        renderBars("Cat kinds", output.breeds, (label) => BREED_NAMES[label] ?? label);
    } else {
        // Not a cat: name the most likely of ImageNet's 1000 classes instead (dog breeds, wild cats, objects…)
        const best = output.top_predictions[0];
        title.textContent = `Not a cat. Looks like a ${best.label} · ${percent(best.probability)}`;
        detail.textContent = `Cat classes only got ${percent(output.cat_score)} in total. The model's top guesses:`;
        renderBars("Top ImageNet classes", output.top_predictions, (label) => label);
    }
    result.hidden = false;
}

classifyButton.addEventListener("click", async () => {
    if (!selectedFile) return;

    classifyButton.disabled = true;
    classifyButton.textContent = "Classifying…";
    showError("");

    const form = new FormData();
    form.append("image", selectedFile);

    try {
        const response = await fetch("/api/classify", { method: "POST", body: form });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Classification failed.");
        renderResult(data);
    } catch (error) {
        result.hidden = true;
        showError(error.message);
    } finally {
        classifyButton.disabled = false;
        classifyButton.textContent = "Classify";
    }
});

// Model status: Cog reports STARTING while setup() loads the weights, then READY
async function checkModel() {
    let status = "UNREACHABLE";
    try {
        status = (await (await fetch("/api/health")).json()).model;
    } catch {
        // the website itself is down; keep UNREACHABLE
    }
    const states = {
        READY: ["ready", "Model ready"],
        STARTING: ["starting", "Model is loading…"],
        BUSY: ["ready", "Model busy"],
    };
    const [className, text] = states[status] ?? ["down", "Model not reachable"];
    modelStatus.className = `status ${className}`;
    modelStatusText.textContent = text;
    setTimeout(checkModel, status === "READY" ? 15000 : 3000);
}
checkModel();
