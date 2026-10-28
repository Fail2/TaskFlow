
const API = {
    tasks: "/tasks",
    chat: "/chat",
    history: "/history"
};

const THREAD_KEY = "taskflow_thread_id";

const taskList = document.getElementById("task-list");
const taskCount = document.getElementById("task-count");
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const sendButton = document.getElementById("send");
const connection = document.getElementById("connection");
const errorBanner = document.getElementById("error-banner");
const retryButton = document.getElementById("retry");
const quickPrompts = document.getElementById("quick-prompts");
const charCount = document.getElementById("char-count");

let lastFailedMessage = "";
let isSending = false;
let currentFilter = "all";

function getThreadId() {
    return localStorage.getItem(THREAD_KEY);
}

function setThreadId(id) {
    if (id) {
        localStorage.setItem(THREAD_KEY, id);
    }
}

async function requestJSON(url, options = {}) {
    const response = await fetch(url, options);

    if (!response.ok) {
        let detail = `Request failed (${response.status})`;

        try {
            const body = await response.json();
            detail = body.detail || detail;
        } catch {
            // Keep the default error message.
        }

        throw new Error(detail);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

function createElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;

    return element;
}

function formatStatus(status) {
    const labels = {
        pending: "To do",
        in_progress: "In progress",
        completed: "Done"
    };

    return labels[status] || status || "To do";
}

function formatPriority(priority) {
    if (!priority) return "Medium";

    return priority.charAt(0).toUpperCase() +
        priority.slice(1).toLowerCase();
}

function renderTasks(tasks) {
    taskList.replaceChildren();

    const filteredTasks = tasks.filter(task => {
        if (currentFilter === "all") return true;
        if (currentFilter === "done") return task.status === "completed";
        if (currentFilter === "progress") return task.status === "in_progress";
        if (currentFilter === "todo") {
            return task.status === "pending" || !task.status;
        }

        return true;
    });

    taskCount.textContent =
        `${filteredTasks.length} task${filteredTasks.length === 1 ? "" : "s"}`;

    if (filteredTasks.length === 0) {
        taskList.append(
            createElement(
                "div",
                "empty",
                tasks.length === 0
                    ? "No tasks yet. Ask your AI assistant to create one."
                    : "No tasks match this view."
            )
        );
        return;
    }

    for (const task of filteredTasks) {
        const card = createElement(
            "article",
            `task${task.status === "completed" ? " done" : ""}`
        );

        const mark = createElement("div", "task-mark");
        mark.textContent = task.status === "completed" ? "✓" : "•";

        const body = createElement("div", "task-body");
        const title = createElement("div", "task-title", task.title);
        body.append(title);

        if (task.description) {
            body.append(
                createElement("div", "task-desc", task.description)
            );
        }

        const meta = createElement("div", "task-meta");

        if (task.id !== undefined) {
            meta.append(
                createElement("span", "task-id", `TSK-${String(task.id).padStart(4, "0")}`)
            );
        }

        meta.append(
            createElement("span", "task-status", formatStatus(task.status))
        );

        if (task.due_date) {
            meta.append(
                createElement("span", "task-due", `Due: ${task.due_date}`)
            );
        }

        body.append(meta);

        const priority = createElement(
            "span",
            `priority ${formatPriority(task.priority)}`,
            formatPriority(task.priority)
        );

        card.append(mark, body, priority);
        taskList.append(card);
    }
}

async function loadTasks() {
    try {
        const data = await requestJSON(API.tasks);
        renderTasks(Array.isArray(data) ? data : (data.tasks || []));
    } catch (error) {
        taskList.replaceChildren(
            createElement(
                "div",
                "empty",
                "Could not load tasks. Check that the server is running."
            )
        );

        console.error("Task loading failed:", error);
    }
}



function formatAssistantResponse(text) {
    const escapeHTML = value =>
        String(value).replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[char]);

    const lines = String(text).split("\n");
    const output = [];
    let listType = null;

    function closeList() {
        if (listType) {
            output.push(`</${listType}>`);
            listType = null;
        }
    }

    function formatInline(text) {
        let html = escapeHTML(text);
        html = html.replace(/`([^`\n]+)`/g, "<code>$1</code>");
        html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        return html;
    }

    function isTableRow(line) {
        return line.trim().startsWith("|") &&
            line.trim().endsWith("|");
    }

    function isSeparator(line) {
        return /^\|?[\s:|-]+\|?$/.test(line.trim()) &&
            line.includes("-");
    }

    function parseCells(line) {
        return line.trim()
            .replace(/^\|/, "")
            .replace(/\|$/, "")
            .split("|")
            .map(cell => cell.trim());
    }

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Markdown table
        if (
            isTableRow(line) &&
            i + 1 < lines.length &&
            isTableRow(lines[i + 1]) &&
            isSeparator(lines[i + 1])
        ) {
            closeList();

            const headers = parseCells(line);
            const rows = [];
            i += 2;

            while (i < lines.length && isTableRow(lines[i])) {
                rows.push(parseCells(lines[i]));
                i++;
            }

            i--;

            output.push('<div class="response-table-wrap"><table class="response-table"><thead><tr>');

            headers.forEach(header => {
                output.push(`<th>${formatInline(header)}</th>`);
            });

            output.push("</tr></thead><tbody>");

            rows.forEach(row => {
                output.push("<tr>");

                headers.forEach((_, index) => {
                    output.push(
                        `<td>${formatInline(row[index] || "")}</td>`
                    );
                });

                output.push("</tr>");
            });

            output.push("</tbody></table></div>");
            continue;
        }

        // Headings
        const heading = line.match(/^(#{1,3})\s+(.+)$/);

        if (heading) {
            closeList();
            const level = heading[1].length === 1 ? 3 : 4;
            output.push(
                `<h${level} class="response-heading">${formatInline(heading[2])}</h${level}>`
            );
            continue;
        }

        // Lists
        const unordered = line.match(/^\s*[-*]\s+(.+)$/);
        const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);

        if (unordered || ordered) {
            const type = unordered ? "ul" : "ol";

            if (listType !== type) {
                closeList();
                output.push(`<${type} class="response-list">`);
                listType = type;
            }

            output.push(`<li>${formatInline((unordered || ordered)[1])}</li>`);
            continue;
        }

        closeList();

        if (line.trim()) {
            output.push(`<p>${formatInline(line)}</p>`);
        }
    }

    closeList();
    return output.join("");
}



function addBubble(role, text, className = "") {
    const bubble = createElement(
        "div",
        `bubble ${role}${className ? ` ${className}` : ""}`
    );

    if (role === "assistant" && !className.includes("error")) {
        bubble.innerHTML = formatAssistantResponse(text);
    } else {
        bubble.textContent = text;
    }

    chatLog.append(bubble);
    chatLog.scrollTop = chatLog.scrollHeight;

    return bubble;
}

function showError(show) {
    errorBanner.hidden = !show;
}

function setSending(sending) {
    isSending = sending;
    sendButton.disabled = sending;
    messageInput.disabled = sending;

    connection.textContent = sending ? "● Thinking…" : "● Ready";
    connection.style.color = sending ? "#8A5A14" : "#2E8B62";
}

async function sendMessage(text) {
    const message = text.trim();

    if (!message || isSending) return;

    lastFailedMessage = message;
    showError(false);

    const welcome = chatLog.querySelector(".welcome");
    if (welcome) welcome.remove();

    addBubble("user", message);

    messageInput.value = "";
    updateCharCount();

    const typing = createElement("div", "typing", "TaskFlow is thinking…");
    chatLog.append(typing);
    chatLog.scrollTop = chatLog.scrollHeight;

    setSending(true);

    try {
        const payload = {
            message,
            thread_id: getThreadId()
        };

        const data = await requestJSON(API.chat, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        typing.remove();

        if (data.thread_id) {
            setThreadId(data.thread_id);
        }

        addBubble("assistant", data.response || "No response received.");

        lastFailedMessage = "";
        showError(false);

        await loadTasks();
    } catch (error) {
        typing.remove();

        addBubble(
            "assistant",
            "I couldn't process that message. Please check your connection and retry.",
            "error"
        );

        showError(true);
        console.error("Chat request failed:", error);
    } finally {
        setSending(false);
        messageInput.focus();
    }
}

async function loadHistory() {
    const threadId = getThreadId();

    if (!threadId) return;

    try {
        const data = await requestJSON(
            `${API.history}/${encodeURIComponent(threadId)}`
        );

        const messages = Array.isArray(data)
            ? data
            : (data.messages || data.history || []);

        if (!messages.length) return;

        chatLog.replaceChildren();

        for (const message of messages) {
            const role = message.role ||
                (message.type === "human" ? "user" :
                    message.type === "ai" ? "assistant" : "");

            const content = message.content;

            if (
                (role === "user" || role === "human") &&
                typeof content === "string"
            ) {
                addBubble("user", content);
            } else if (
                (role === "assistant" || role === "ai") &&
                typeof content === "string"
            ) {
                addBubble("assistant", content);
            }
        }
    } catch (error) {
        // A missing or expired history should not prevent new chats.
        console.warn("Could not restore chat history:", error);
    }
}

function updateCharCount() {
    charCount.textContent = `${messageInput.value.length}/1000`;
}

chatForm.addEventListener("submit", event => {
    event.preventDefault();
    sendMessage(messageInput.value);
});

messageInput.addEventListener("input", updateCharCount);

messageInput.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();

        if (!isSending) {
            chatForm.requestSubmit();
        }
    }
});

quickPrompts.addEventListener("click", event => {
    const button = event.target.closest("button[data-prompt]");

    if (!button || isSending) return;

    sendMessage(button.dataset.prompt);
});

retryButton.addEventListener("click", () => {
    if (lastFailedMessage && !isSending) {
        sendMessage(lastFailedMessage);
    }
});

loadTasks();
loadHistory();
updateCharCount();
