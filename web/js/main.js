// =================================================================
// MAIN APPLICATION LOGIC (Runs after the document is loaded)
// =================================================================
document.addEventListener("DOMContentLoaded", function() {
    
    // The App object holds all shared elements, state, and global functions.
    // This keeps the global namespace clean and makes dependencies explicit.
    const App = {
        elements: {},
        state: {},
        globals: {}
    };

    // --- 1. Element Selections ---
    App.elements = {
        body: document.body,
        backgroundContainer: document.querySelector('.background-container'),
        inputForm: document.querySelector(".input-form"),
        messageInput: document.getElementById("main-input"),
        chatDisplay: document.querySelector(".chat-display"),
        backButton: document.getElementById("back-button"),
        contentBody: document.querySelector(".content-body"),
        weatherWidgetContainer: document.getElementById("weather-widget-container"),
        footerTempContainer: document.getElementById("footer-temp-container"),
        themeSelector: document.getElementById("theme-selector"),
        recordButton: document.getElementById("record-button"),
        monitorToggle: document.getElementById("monitor-toggle"),
        healthMonitorToggle: document.getElementById("health-monitor-toggle"),
        notificationsButton: document.getElementById("notifications-button"),
        notificationsPanel: document.getElementById("notifications-panel"),
        notificationsList: document.getElementById("notifications-list"),
        notificationDot: document.getElementById("notification-dot"),
        inboxButton: document.getElementById("inbox-button"),
        inboxPanel: document.getElementById("inbox-panel"),
        inboxList: document.getElementById("inbox-list"),
        inboxDot: document.getElementById("inbox-dot"),
        emailViewerModal: document.getElementById("email-viewer-modal"),
        emailViewerCloseBtn: document.getElementById("email-viewer-close-btn"),
        emailViewerFrom: document.getElementById("email-viewer-from"),
        emailViewerSubject: document.getElementById("email-viewer-subject"),
        emailViewerBody: document.getElementById("email-viewer-body"),
        emailViewerOpenBtn: document.getElementById("email-viewer-open-btn"),
        profileBtn: document.getElementById('profile-btn'),
        profileModal: document.getElementById('profile-modal'),
        profileCloseBtn: document.getElementById('profile-close-btn'),
        openSettingsBtn: document.getElementById('open-settings-btn'),
        profileSaveBtn: document.getElementById('profile-save-btn'),
        profilePicDisplay: document.getElementById('profile-pic-display'),
        profilePicInput: document.getElementById('profile-pic-input'),
        profileNameInput: document.getElementById('profile-name-input'),
        greetingElement: document.getElementById('greeting'),
        settingsOverlay: document.getElementById('settings-overlay'),
        settingsBackBtn: document.getElementById('settings-back-btn'),
        settingsSaveBtn: document.getElementById('settings-save-btn'),
        visualQueryOverlay: document.getElementById('visual-query-overlay'),
        visualQueryInput: document.getElementById('visual-query-input'),
        welcomeNotificationsButton: document.getElementById("welcome-notifications-button"),
        welcomeNotificationDot: document.getElementById("welcome-notification-dot"),
        welcomeInboxButton: document.getElementById("welcome-inbox-button"),
        welcomeInboxDot: document.getElementById("welcome-inbox-dot"),
        confirmationModal: document.getElementById('confirmationModal'),
        confirmationTitle: document.getElementById('confirmationTitle'),
        confirmationDetails: document.getElementById('confirmationDetails'),
        confirmBtn: document.getElementById('confirmBtn'),
        cancelBtn: document.getElementById('cancelBtn'),
        historyButton: document.getElementById('history-button'),
        briefingButton: document.getElementById('briefing-button'),
        briefingPanel: document.getElementById('briefing-notifications-panel'),
        historySidebar: document.getElementById('history-sidebar'),
        closeHistoryBtn: document.getElementById('close-history-btn'),
        historyOverlay: document.getElementById('history-overlay'),
        historyList: document.getElementById('history-list'),
        deleteConfirmModal: document.getElementById('delete-confirm-modal'),
        deleteConfirmMessage: document.getElementById('delete-confirm-message'),
        deleteConfirmBtn: document.getElementById('delete-confirm-btn'),
        deleteCancelBtn: document.getElementById('delete-cancel-btn'),
        agentStatusBar: document.getElementById('agent-status-bar'),
    };

    // --- 2. State Variables ---
    App.state = {
        currentThemeMode: 'auto',
        isRecording: false,
        mediaRecorder: null,
        audioChunks: [],
        isPanelOpen: false,
        isInboxOpen: false,
        currentEmailWebLink: null
    };

    // --- 3. Initialize Modules ---
    // Pass the App object to each initializer. They will populate App.globals
    // and attach their specific event listeners.
    initThemeHandler(App);
    initChatHandler(App);
    initComponents(App);
    initHistoryHandler(App);

    // --- 4. Assign Global Functions ---
    // This connects the functions defined in our modules to the globally-scoped
    // forward declarations required by eel_bindings.js.
    setChatActive = App.globals.setChatActive;
    startRecording = App.globals.startRecording;
    stopRecording = App.globals.stopRecording;
    scrollToBottom = App.globals.scrollToBottom;
    processApiResponse = App.globals.processApiResponse;

    // --- 5. Top-Level Event Listeners ---
    App.elements.backButton.addEventListener("click", () => {
        setChatActive(false);
        // Clear the chat display and input field after transition
        App.elements.agentStatusBar.textContent = ''; 
        setTimeout(() => { 
            App.elements.chatDisplay.innerHTML = ''; 
            App.elements.messageInput.value = '';
        }, 500); 
        // Tell the backend to start a new chat session
        eel.start_new_chat_session(); 
    });
});