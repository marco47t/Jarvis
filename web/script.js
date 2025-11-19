document.addEventListener("DOMContentLoaded", function() {
    // --- Element Selections ---
    const body = document.body;
    const backgroundContainer = document.querySelector('.background-container');
    const inputForm = document.querySelector(".input-form");
    const messageInput = document.getElementById("main-input");
    const chatDisplay = document.querySelector(".chat-display");
    const backButton = document.getElementById("back-button");
    const mainContent = document.querySelector(".main-content");
    const contentBody = document.querySelector(".content-body");
    const weatherWidgetContainer = document.getElementById("weather-widget-container");
    const footerTempContainer = document.getElementById("footer-temp-container");
    const themeSelector = document.getElementById("theme-selector");
    const recordButton = document.getElementById("record-button");
    const monitorToggle = document.getElementById("monitor-toggle");
    const healthMonitorToggle = document.getElementById("health-monitor-toggle");
    // Notifications Panel
    const notificationsButton = document.getElementById("notifications-button");
    const notificationsPanel = document.getElementById("notifications-panel");
    const notificationsList = document.getElementById("notifications-list");
    const notificationDot = document.getElementById("notification-dot");
    // Inbox Panel
    const inboxButton = document.getElementById("inbox-button");
    const inboxPanel = document.getElementById("inbox-panel");
    const inboxList = document.getElementById("inbox-list");
    const inboxDot = document.getElementById("inbox-dot");
    // Email Viewer Modal
    const emailViewerModal = document.getElementById("email-viewer-modal");
    const emailViewerCloseBtn = document.getElementById("email-viewer-close-btn");
    const emailViewerFrom = document.getElementById("email-viewer-from");
    const emailViewerSubject = document.getElementById("email-viewer-subject");
    const emailViewerBody = document.getElementById("email-viewer-body");
    // Profile & Settings
    const profileBtn = document.getElementById('profile-btn');
    const profileModal = document.getElementById('profile-modal');
    const profileCloseBtn = document.getElementById('profile-close-btn');
    const openSettingsBtn = document.getElementById('open-settings-btn');
    const profileSaveBtn = document.getElementById('profile-save-btn');
    const profilePicDisplay = document.getElementById('profile-pic-display');
    const profilePicInput = document.getElementById('profile-pic-input');
    const profileNameInput = document.getElementById('profile-name-input');
    const greetingElement = document.getElementById('greeting');
    const settingsOverlay = document.getElementById('settings-overlay');
    const settingsBackBtn = document.getElementById('settings-back-btn');
    const settingsSaveBtn = document.getElementById('settings-save-btn');

    // --- State Variables ---
    let isChatActive = false;
    let currentThemeMode = 'auto';
    let isRecording = false;
    let mediaRecorder;
    let audioChunks = [];
    let isPanelOpen = false;
    let isInboxOpen = false;

    // --- Function exposed to Python for the shortcut ---
    eel.expose(toggle_recording_from_shortcut);
    function toggle_recording_from_shortcut() {
        if (!isRecording) { startRecording(); }
        else { stopRecording(); }
    }

    // --- Custom Toast Notification Function ---
    function showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            console.error("Toast container not found!");
            return;
        }
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('removing');
            toast.addEventListener('animationend', () => { toast.remove(); });
        }, 4000);
    }

    // --- UI State Management ---
    function setChatActive(isActive) {
        isChatActive = isActive;
        body.classList.toggle('chat-active', isChatActive);
    }

    // --- Widget Display Function ---
    function displayWeather(data) {
        if (!data || data.error || data.status === 'error') {
            console.error("Weather data error:", data.message || data.error);
            weatherWidgetContainer.innerHTML = '';
            if (!isChatActive) { footerTempContainer.innerHTML = ''; }
            return;
        }
        const iconHTML = `<div class="weather-card"><div class="weather-icon"><img src="${data.condition_icon}" alt="${data.condition_text}"></div></div>`;
        weatherWidgetContainer.innerHTML = iconHTML;
        if (!isChatActive) {
            const tempHTML = `<p class="footer-temp">${Math.round(data.temp_c)}°</p>`;
            footerTempContainer.innerHTML = tempHTML;
        }
    }

   healthMonitorToggle.addEventListener('change', function() {
        const isEnabled = this.checked;
        eel.toggle_health_monitoring(isEnabled)();
        if (isEnabled) { addSystemMessage("System health monitoring activated."); }
        else { addSystemMessage("System health monitoring deactivated."); }
    });

    // --- Theme Selection Logic ---
    function updateTheme(data) {
        let themeClass = '';
        if (currentThemeMode === 'auto') {
            if (!data || data.error || data.status === 'error') {
                body.className = isChatActive ? 'chat-active' : '';
                backgroundContainer.className = 'background-container';
                return;
            }
            const condition = data.condition_text.toLowerCase();
            const isDay = data.is_day === 1;
            const hour = parseInt(data.localtime.split(' ')[1].split(':')[0]);
            if (isDay && (hour >= 6 && hour < 9)) { themeClass = 'theme-sunrise'; }
            else if (isDay && (hour >= 18 && hour < 20)) { themeClass = 'theme-sunset'; }
            else if (isDay && condition.includes("partly cloudy")) { themeClass = 'theme-day-partly-cloudy'; }
            else if (condition.includes("sunny") || condition.includes("clear")) { themeClass = isDay ? 'theme-day-clear' : 'theme-night-clear'; }
            else if (condition.includes("cloudy") || condition.includes("overcast")) { themeClass = isDay ? 'theme-day-cloudy' : 'theme-night-cloudy'; }
            else if (condition.includes("rain") || condition.includes("drizzle") || condition.includes("thundery")) { themeClass = 'theme-rain'; }
            else if (condition.includes("snow") || condition.includes("sleet") || condition.includes("ice") || condition.includes("blizzard")) { themeClass = 'theme-snow'; }
            else if (condition.includes("mist") || condition.includes("fog")) { themeClass = 'theme-mist'; }
            else { themeClass = isDay ? 'theme-day-clear' : 'theme-night-clear'; }
        } else {
            themeClass = currentThemeMode;
        }
        body.className = themeClass;
        if (isChatActive) { body.classList.add('chat-active'); }
        backgroundContainer.className = 'background-container ' + themeClass;
    }

    function addSystemMessage(message) {
        if (!isChatActive) { setChatActive(true); }
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", "system-message");
        messageElement.innerHTML = `⚙️ <i>${message}</i>`;
        chatDisplay.appendChild(messageElement);
        scrollToBottom();
    }

    // --- Email Viewer Logic ---
    async function openEmailViewer(emailId) {
        if (!emailId) return;

        emailViewerFrom.textContent = 'Loading...';
        emailViewerSubject.textContent = 'Loading...';
        emailViewerBody.textContent = 'Fetching email content...';
        emailViewerModal.classList.add('active');

        try {
            const details = await eel.get_email_content(emailId)();
            if (details.error) {
                emailViewerBody.textContent = details.error;
            } else {
                emailViewerFrom.textContent = details.from;
                emailViewerSubject.textContent = details.subject;
                emailViewerBody.textContent = details.body;
            }
        } catch (err) {
            console.error("Failed to fetch email content:", err);
            emailViewerBody.textContent = "An error occurred while fetching the email.";
        }
    }

    function closeEmailViewer() {
        emailViewerModal.classList.remove('active');
    }
    emailViewerCloseBtn.addEventListener('click', closeEmailViewer);
    emailViewerModal.addEventListener('click', (e) => {
        if (e.target === emailViewerModal) {
            closeEmailViewer();
        }
    });

    // --- Notifications & Inbox Panels Logic ---
    function toggleNotificationsPanel() {
        isPanelOpen = !isPanelOpen;
        notificationsPanel.classList.toggle('visible', isPanelOpen);
        if (isPanelOpen) {
            notificationDot.classList.remove('visible');
            updateNotifications();
        }
    }

    async function updateNotifications() {
        const systemNotifications = await eel.get_monitor_notifications()();
        const importantEmails = await eel.get_important_emails()();

        const allNotifications = [
            ...systemNotifications.map(n => ({ ...n, type: 'system', from: 'System Monitor', subject: n.text })),
            ...importantEmails.map(e => ({ ...e, type: 'email' }))
        ];

        if (allNotifications.length > 0 && !isPanelOpen) {
            notificationDot.classList.add('visible');
        } else if (allNotifications.length === 0) {
            notificationDot.classList.remove('visible');
        }
        
        if (!isPanelOpen) return;
        
        const incomingIds = new Set(allNotifications.map(n => n.id));
        notificationsList.querySelectorAll('li').forEach(li => {
            if (!incomingIds.has(li.dataset.id)) { li.remove(); }
        });
        
        allNotifications.forEach(notification => {
            if (!document.querySelector(`#notifications-list li[data-id='${notification.id}']`)) {
                const li = document.createElement('li');
                li.dataset.id = notification.id;
                li.dataset.type = notification.type;
                
                const dismissBtn = document.createElement('span');
                dismissBtn.className = 'dismiss-btn';
                dismissBtn.innerHTML = '&times;';
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'notification-content';

                const icon = notification.type === 'email' ? '📧' : '⚙️';

                contentDiv.innerHTML = `
                    <span class="notification-sender">${icon} ${notification.from || notification.from_full}</span>
                    <span class="notification-subject">${notification.subject}</span>
                `;
                
                li.appendChild(contentDiv);
                li.appendChild(dismissBtn);
                notificationsList.appendChild(li);
            }
        });

        if (notificationsList.children.length === 0) {
            notificationsList.innerHTML = '<li>No important notifications.</li>';
        }
    }
    
    notificationsList.addEventListener('click', function(event) {
        const li = event.target.closest('li');
        if (!li || !li.dataset.id) return;
        
        const id = li.dataset.id;
        const type = li.dataset.type;

        if (event.target.classList.contains('dismiss-btn')) {
            event.stopPropagation();
            li.classList.add('removing');
            (type === 'email' ? eel.dismiss_email(id) : eel.dismiss_notification(id))();
            li.addEventListener('animationend', () => {
                li.remove();
                if (notificationsList.children.length === 0) {
                    notificationsList.innerHTML = '<li>No important notifications.</li>';
                }
            });
        } else if (type === 'email') {
            openEmailViewer(id);
        }
    });
    
    notificationsButton.addEventListener('click', toggleNotificationsPanel);

    function toggleInboxPanel() {
        isInboxOpen = !isInboxOpen;
        inboxPanel.classList.toggle('visible', isInboxOpen);
        if (isInboxOpen) {
            inboxDot.classList.remove('visible');
            updateInbox();
        }
    }

    async function updateInbox() {
        const otherEmails = await eel.get_other_emails()();

        if (otherEmails.length > 0 && !isInboxOpen) {
            inboxDot.classList.add('visible');
        } else if (otherEmails.length === 0) {
            inboxDot.classList.remove('visible');
        }
        
        if (!isInboxOpen) return;

        const incomingIds = new Set(otherEmails.map(e => e.id));
        inboxList.querySelectorAll('li').forEach(li => {
            if (!incomingIds.has(li.dataset.id)) { li.remove(); }
        });
        
        otherEmails.forEach(email => {
            if (!document.querySelector(`#inbox-list li[data-id='${email.id}']`)) {
                const li = document.createElement('li');
                li.dataset.id = email.id;
                
                const dismissBtn = document.createElement('span');
                dismissBtn.className = 'dismiss-btn';
                dismissBtn.innerHTML = '&times;';
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'email-content';
                contentDiv.innerHTML = `
                    <span class="email-sender">${email.from_full}</span>
                    <span class="email-subject">${email.subject}</span>
                `;
                
                li.appendChild(contentDiv);
                li.appendChild(dismissBtn);
                inboxList.appendChild(li);
            }
        });

        if (inboxList.children.length === 0) {
            inboxList.innerHTML = '<li>No new mail.</li>';
        }
    }
    
    inboxList.addEventListener('click', function(event) {
        const li = event.target.closest('li');
        if (!li || !li.dataset.id) return;

        const id = li.dataset.id;

        if (event.target.classList.contains('dismiss-btn')) {
            event.stopPropagation();
            li.classList.add('removing');
            eel.dismiss_email(id)();
            li.addEventListener('animationend', () => {
                 li.remove();
                 if (inboxList.children.length === 0) {
                    inboxList.innerHTML = '<li>No new mail.</li>';
                 }
            });
        } else {
            openEmailViewer(id);
        }
    });

    inboxButton.addEventListener('click', toggleInboxPanel);

    // --- Main Fetch/Update Loop ---
    setInterval(() => {
        updateNotifications();
        updateInbox();
    }, 5000);
    
    async function fetchAndUpdateWeather() {
        try {
            const weatherData = await eel.get_latest_weather_data()();
            displayWeather(weatherData);
            updateTheme(weatherData);
        } catch (error) {
            console.error("Failed to fetch weather data:", error);
            updateTheme(null);
        }
    }
    fetchAndUpdateWeather(); // Initial call

    // --- Helper Functions ---
    function scrollToBottom() { setTimeout(() => { contentBody.scrollTop = contentBody.scrollHeight; }, 50); }
    
    function addUserMessage(message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", "user-message");
        messageElement.textContent = message;
        chatDisplay.appendChild(messageElement);
        scrollToBottom();
    }
    
    function showThinkingIndicator() {
        const thinkingElement = document.createElement("div");
        thinkingElement.id = "thinking-indicator";
        thinkingElement.classList.add("chat-message", "ai-message", "thinking");
        thinkingElement.innerHTML = `<span></span><span></span><span></span>`;
        chatDisplay.appendChild(thinkingElement);
        scrollToBottom();
    }
    
    function typewriterEffect(element, text, onComplete) {
        let i = 0;
        element.innerHTML = "";
        element.classList.add("typing-cursor");
        const typingInterval = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                scrollToBottom();
            } else {
                clearInterval(typingInterval);
                element.classList.remove("typing-cursor");
                if (onComplete) { onComplete(); }
            }
        }, 20);
    }
    
    function processApiResponse(text) {
        const thinkingIndicator = document.getElementById("thinking-indicator");
        if (thinkingIndicator) { thinkingIndicator.remove(); }
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", "ai-message");
        chatDisplay.appendChild(messageElement);
        const onTypingComplete = () => {
            const converter = new showdown.Converter({ noHeaderId: true, simpleLineBreaks: true, strikethrough: true, tables: true });
            messageElement.innerHTML = converter.makeHtml(text);
            messageElement.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
            scrollToBottom();
        };
        typewriterEffect(messageElement, text, onTypingComplete);
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
    
    monitorToggle.addEventListener('change', function() {
        const isEnabled = this.checked;
        eel.toggle_monitoring(isEnabled)();
        if (isEnabled) { addSystemMessage("Downloads folder monitoring activated."); }
        else { addSystemMessage("Downloads folder monitoring deactivated."); }
    });

    // --- Voice Recording Functions ---
    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            isRecording = true;
            recordButton.classList.add('recording');
            messageInput.placeholder = "Recording... Press shortcut to stop.";
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            mediaRecorder.ondataavailable = (event) => { audioChunks.push(event.data); };
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const audioDataBuffer = await audioBlob.arrayBuffer();
                const audioData_base64 = arrayBufferToBase64(audioDataBuffer);
                if (!isChatActive) { setChatActive(true); }
                addUserMessage("🎤 Voice message...");
                showThinkingIndicator();
                try {
                    const result = await eel.process_audio_recording(audioData_base64)();
                    const userMessages = document.querySelectorAll('.user-message');
                    userMessages[userMessages.length - 1].textContent = result.transcription;
                    processApiResponse(result.final_answer);
                } catch (error) {
                    console.error("Error processing audio:", error);
                    processApiResponse("Sorry, there was an error transcribing your voice message.");
                }
                audioChunks = [];
            };
        } catch (err) {
            console.error("Error accessing microphone:", err);
            messageInput.placeholder = "Microphone access denied.";
            isRecording = false;
        }
    }
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === "recording") { mediaRecorder.stop(); }
        isRecording = false;
        recordButton.classList.remove('recording');
        messageInput.placeholder = "Press Enter to send...";
    }

    // --- Event Listeners ---
    themeSelector.addEventListener('change', (event) => {
        currentThemeMode = event.target.value;
        fetchAndUpdateWeather();
    });
    recordButton.addEventListener('click', () => {
        if (!isRecording) { startRecording(); }
        else { stopRecording(); }
    });
    function sendMessage() {
        const messageText = messageInput.value.trim();
        if (messageText === "") { return; }
        if (!isChatActive) { setChatActive(true); }
        addUserMessage(messageText);
        messageInput.value = "";
        showThinkingIndicator();
        eel.run_agent_think(messageText)().then((final_answer) => {
            processApiResponse(final_answer);
        }).catch((error) => {
            console.error("An error occurred with the Eel call:", error);
            processApiResponse("Sorry, an error occurred while connecting to the agent.");
        });
    }
    inputForm.addEventListener("submit", function(event) { event.preventDefault(); });
    messageInput.addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });
    backButton.addEventListener("click", () => {
        setChatActive(false);
        setTimeout(() => { chatDisplay.innerHTML = ''; }, 500);
    });

    // =================================================================
    // PROFILE AND SETTINGS LOGIC
    // =================================================================
    const settingsMapping = {
        'GEMINI_API_KEY': 'setting-gemini-api-key', 'TELEGRAM_BOT_TOKEN': 'setting-telegram-bot-token',
        'TELEGRAM_ADMIN_USER_ID': 'setting-telegram-admin-id', 'WEATHER_API_KEY': 'setting-weather-api-key',
        'DEFAULT_AI_MODEL': 'setting-default-ai-model', 'VISION_MODEL_NAME': 'setting-vision-model-name',
        'GOOGLE_CSE_API_KEY': 'setting-google-cse-api-key', 'GOOGLE_CSE_ENGINE_ID': 'setting-google-cse-engine-id',
        'AI_TEMPERATURE': 'setting-ai-temperature', 'MAX_WEB_SCRAPE_CONTENT_LENGTH': 'setting-max-scrape-length'
    };

    function openProfileModal() {
        setChatActive(false);
        profileModal.classList.add('active');
    }
    function closeProfileModal() {
        profileModal.classList.remove('active');
        if (chatDisplay.children.length > 0) {
            setChatActive(true);
        }
    }
    profileBtn.addEventListener('click', openProfileModal);
    profileCloseBtn.addEventListener('click', closeProfileModal);

    openSettingsBtn.addEventListener('click', () => {
        profileModal.classList.remove('active');
        settingsOverlay.classList.add('active');
    });

    settingsBackBtn.addEventListener('click', () => {
        settingsOverlay.classList.remove('active');
        profileModal.classList.add('active');
    });

    function closeAllModalsAndReturn() {
        profileModal.classList.remove('active');
        settingsOverlay.classList.remove('active');
        if (chatDisplay.children.length > 0) {
            setChatActive(true);
        } else {
            setChatActive(false);
        }
    }
    profileModal.addEventListener('click', (e) => {
        if (e.target === profileModal) { closeAllModalsAndReturn(); }
    });
    settingsOverlay.addEventListener('click', (e) => {
        if (e.target === settingsOverlay) { closeAllModalsAndReturn(); }
    });

    async function loadProfileData() {
        const profileData = await eel.get_profile_data()();
        if (profileData) {
            profileNameInput.value = profileData.name || 'User';
            greetingElement.textContent = `Hello, ${profileData.name || 'User'}`;
            if (profileData.photo_base64) {
                const imageUrl = `data:image/jpeg;base64,${profileData.photo_base64}`;
                profilePicDisplay.style.backgroundImage = `url('${imageUrl}')`;
                profileBtn.style.backgroundImage = `url('${imageUrl}')`;
            } else {
                profilePicDisplay.style.backgroundImage = 'none';
                profileBtn.style.backgroundImage = 'none';
            }
        }
    }

    async function loadSettingsData() {
        const settings = await eel.get_settings()();
        if (settings) {
            for (const key in settingsMapping) {
                const element = document.getElementById(settingsMapping[key]);
                if (element) { element.value = settings[key] || ''; }
            }
        }
    }

    profilePicDisplay.addEventListener('click', () => profilePicInput.click());
    let newPhotoBase64 = null;
    profilePicInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                profilePicDisplay.style.backgroundImage = `url('${e.target.result}')`;
                newPhotoBase64 = e.target.result.split(',')[1];
            };
            reader.readAsDataURL(file);
        }
    });

    profileSaveBtn.addEventListener('click', async () => {
        const profileDataToSave = { name: profileNameInput.value };
        if (newPhotoBase64) { profileDataToSave.photo_base64 = newPhotoBase64; }
        const success = await eel.save_profile_data(profileDataToSave)();
        if (success) {
            showToast('Profile saved successfully!', 'success');
            newPhotoBase64 = null;
            await loadProfileData();
            closeProfileModal();
        } else {
            showToast('Error saving profile.', 'error');
        }
    });

    settingsSaveBtn.addEventListener('click', async () => {
        const settingsToSave = {};
        for (const key in settingsMapping) {
            const element = document.getElementById(settingsMapping[key]);
            if (element) { settingsToSave[key] = element.value; }
        }
        const result = await eel.save_settings(settingsToSave)();
        if (result && result.success) {
            showToast(result.message || 'Settings saved!', 'success');
            settingsOverlay.classList.remove('active');
            if (chatDisplay.children.length > 0) {
                setChatActive(true);
            } else {
                setChatActive(false);
            }
        } else {
            showToast('An error occurred while saving settings.', 'error');
        }
    });

    // --- Initial Data Load on Startup ---
    loadProfileData();
    loadSettingsData();

}); // --- END OF DOMContentLoaded ---