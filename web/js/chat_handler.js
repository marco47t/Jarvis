function initChatHandler(App) {
    const { elements, state, globals } = App;

    // --- Helper Functions ---
    globals.scrollToBottom = () => {
        setTimeout(() => { elements.contentBody.scrollTop = elements.contentBody.scrollHeight; }, 50);
    }

    function updateAgentStatus(message) {
        if (elements.agentStatusBar) {
            elements.agentStatusBar.textContent = message;
        }
    }
    // Expose it to Python under the name 'update_agent_status'
    eel.expose(updateAgentStatus, 'update_agent_status');

    function addUserMessage(message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", "user-message");
        messageElement.textContent = message;
        elements.chatDisplay.appendChild(messageElement);
        globals.scrollToBottom();
    }
    globals.addUserMessage = addUserMessage; // <-- NEW: Expose the function globally

    function showThinkingIndicator() {
        if (document.getElementById("thinking-indicator")) return;
        const thinkingElement = document.createElement("div");
        thinkingElement.id = "thinking-indicator";
        thinkingElement.classList.add("chat-message", "ai-message", "thinking");
        thinkingElement.innerHTML = `<span></span><span></span><span></span>`;
        elements.chatDisplay.appendChild(thinkingElement);
        globals.scrollToBottom();
    }

    function arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }
    
    // --- Global Function Assignments ---
    globals.setChatActive = (isActive) => {
        isChatActive = isActive; // isChatActive is a global from eel_bindings.js
        elements.body.classList.toggle('chat-active', isChatActive);
    };

    globals.processApiResponse = (text) => {
        const thinkingIndicator = document.getElementById("thinking-indicator");
        if (thinkingIndicator) { thinkingIndicator.remove(); }

        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", "ai-message");
        elements.chatDisplay.appendChild(messageElement);

        const converter = new showdown.Converter({ noHeaderId: true, simpleLineBreaks: true, strikethrough: true, tables: true });
        messageElement.innerHTML = converter.makeHtml(text);
        
        messageElement.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        globals.scrollToBottom();
        updateAgentStatus('Ready.');
        elements.messageInput.disabled = false;
        elements.recordButton.disabled = false;
        elements.messageInput.placeholder = "Press Enter to send...";
        elements.messageInput.focus();
    };

    // --- Voice Recording Functions ---
    globals.startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            state.isRecording = true;
            elements.recordButton.classList.add('recording');
            elements.messageInput.placeholder = "Recording... Press shortcut or button to stop.";
            state.mediaRecorder = new MediaRecorder(stream);
            state.mediaRecorder.start();
            state.mediaRecorder.ondataavailable = (event) => { state.audioChunks.push(event.data); };
            state.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
                const audioDataBuffer = await audioBlob.arrayBuffer();
                const audioData_base64 = arrayBufferToBase64(audioDataBuffer);
                
                if (!isChatActive) { globals.setChatActive(true); }
                addUserMessage("🎤 Voice message...");
                
                elements.messageInput.disabled = true;
                elements.recordButton.disabled = true;
                elements.messageInput.placeholder = "Agent is working...";
                showThinkingIndicator();

                try {
                    const result = await eel.process_audio_recording(audioData_base64)();
                    const userMessages = document.querySelectorAll('.user-message');
                    userMessages[userMessages.length - 1].textContent = result.transcription;
                    globals.processApiResponse(result.final_answer);
                } catch (error) {
                    globals.processApiResponse("Sorry, there was an error transcribing your voice message.");
                }
                state.audioChunks = [];
            };
        } catch (err) {
            elements.messageInput.placeholder = "Microphone access denied.";
            state.isRecording = false;
        }
    }
    
    globals.stopRecording = () => {
        if (state.mediaRecorder && state.mediaRecorder.state === "recording") { state.mediaRecorder.stop(); }
        state.isRecording = false;
        elements.recordButton.classList.remove('recording');
    }

    // --- Message Sending ---
    function sendMessage() {
        const messageText = elements.messageInput.value.trim();
        if (messageText === "") return;
        if (!isChatActive) globals.setChatActive(true);
        addUserMessage(messageText);
        elements.messageInput.value = "";
        updateAgentStatus('Agent is activating...');
        elements.messageInput.disabled = true;
        elements.recordButton.disabled = true;
        elements.messageInput.placeholder = "Agent is working...";
        showThinkingIndicator();
        
        eel.run_agent_think(messageText)().then(globals.processApiResponse).catch((error) => {
            console.error(error);
            globals.processApiResponse("Sorry, an error occurred while connecting to the agent.");
        });
    }

    // --- Event Listeners ---
    elements.inputForm.addEventListener("submit", (e) => { e.preventDefault(); sendMessage(); });

    elements.messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    elements.messageInput.addEventListener('focus', () => {
        if (!isChatActive) globals.setChatActive(true);
    });

    elements.recordButton.addEventListener('click', () => {
        if (!isChatActive) globals.setChatActive(true);
        if (!state.isRecording) { globals.startRecording(); }
        else { globals.stopRecording(); }
    });
}
