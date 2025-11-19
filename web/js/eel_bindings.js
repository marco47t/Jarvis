// =================================================================
// GLOBALLY EXPOSED FUNCTIONS (Called by Python)
// These MUST be in the global scope, outside of any event listeners.
// =================================================================

// --- Global State for Eel ---
let isChatActive = false;
let capturedImageBase64 = null;

// --- Exposed Functions ---
eel.expose(toggle_recording_from_shortcut);
function toggle_recording_from_shortcut() {
    const recordButton = document.getElementById("record-button");
    if (!recordButton) return; // Guard against element not ready
    if (!recordButton.classList.contains('recording')) {
        startRecording();
    } else {
        stopRecording();
    }
}

eel.expose(showVisualQueryPrompt);
function showVisualQueryPrompt(image_base_64) {
    const visualQueryOverlay = document.getElementById('visual-query-overlay');
    const visualQueryInput = document.getElementById('visual-query-input');
    if (!visualQueryOverlay || !visualQueryInput) return;

    capturedImageBase64 = image_base_64;
    visualQueryOverlay.classList.add('visible');
    visualQueryInput.focus();
}

eel.expose(activateAndShowChat);
function activateAndShowChat() {
    if (!isChatActive) {
        setChatActive(true);
    }
}

eel.expose(displayVisualQueryResult);
function displayVisualQueryResult(image_base_64, prompt, answer) {
    const chatDisplay = document.querySelector(".chat-display");
    if (!chatDisplay) return;

    const userMessageElement = document.createElement("div");
    userMessageElement.classList.add("chat-message", "user-message", "visual-query");
    userMessageElement.innerHTML = `
        <p class="visual-query-prompt">${prompt}</p>
        <img src="data:image/png;base64,${image_base_64}" alt="Captured region" class="visual-query-image">
    `;
    chatDisplay.appendChild(userMessageElement);
    scrollToBottom();

    processApiResponse(answer);
}

eel.expose(prompt_user_for_confirmation);
function prompt_user_for_confirmation(details) {
    const event = new CustomEvent('show-confirmation-modal', { detail: details });
    document.dispatchEvent(event);
}

// --- Forward Declarations ---
// These are placeholders for functions that will be defined in other files
// and assigned in main.js. This allows the globally exposed functions above
// to call them safely.
let setChatActive;
let startRecording;
let stopRecording;
let scrollToBottom;
let processApiResponse;