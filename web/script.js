(() => {
  const form = document.querySelector("#chat-form");
  const input = document.querySelector("#message-input");
  const messages = document.querySelector("#messages");
  const newTripButton = document.querySelector("#new-trip");
  const examplePromptButton = document.querySelector("#example-prompt");
  const welcomeMessage = messages.innerHTML;
  const sessionKey = "triptales-session-id";
  const examplePrompt = "I want to visit Dubai for 5 days in December with my family (2 adults, 2 children). Our total budget is 800,000 PKR. We prefer a relaxed schedule and need halal food. We enjoy beaches and shopping. Please also guide me on the visa and flights.";
  let activeRequest = null;

  const getSessionId = () => {
    let id = sessionStorage.getItem(sessionKey);
    if (!id) {
      id = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      sessionStorage.setItem(sessionKey, id);
    }
    return id;
  };

  const scrollToLatest = () => {
    messages.scrollTop = messages.scrollHeight;
  };

  const resizeInput = () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
  };

  const hasTableOrItinerary = (markdown) => {
    const lines = markdown.split(/\r?\n/).map((line) => line.trim());
    const hasTable = lines.some((line, index) =>
      /^\|.+\|$/.test(line) && /^\|[\s:|-]+\|$/.test(lines[index + 1] || "")
    );
    const hasPlanHeading = /^\s*#{1,6}\s+.*\b(?:itinerary|(?:travel|trip) plan)\b/im.test(markdown);
    const daySections = markdown.match(/(?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*)?day\s+\d+\b/gim) || [];
    return hasTable || hasPlanHeading || daySections.length > 1;
  };

  const addUserMessage = (text) => {
    const article = document.createElement("article");
    article.className = "message user-message";
    const content = document.createElement("div");
    content.className = "message-content";
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = text;
    content.append(bubble);
    article.append(content);
    messages.append(article);
    scrollToLatest();
  };

  const addAgentMessage = (markdown, { isError = false } = {}) => {
    const article = document.createElement("article");
    article.className = "message agent-message";
    const avatar = document.createElement("span");
    avatar.className = "message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "🌍";

    const content = document.createElement("div");
    content.className = "message-content";
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    if (isError) bubble.classList.add("warning-bubble");
    if (window.marked && window.DOMPurify) {
      bubble.innerHTML = window.DOMPurify.sanitize(window.marked.parse(markdown, { breaks: true }));
    } else {
      bubble.textContent = markdown;
    }

    content.append(bubble);
    if (!isError && hasTableOrItinerary(markdown)) {
      const actions = document.createElement("div");
      actions.className = "message-actions";
      const download = document.createElement("button");
      download.type = "button";
      download.className = "download-button";
      download.textContent = "↓  Download plan as PDF";
      download.addEventListener("click", () => downloadPdf(markdown, download));
      actions.append(download);
      content.append(actions);
    }
    article.append(avatar, content);
    messages.append(article);
    scrollToLatest();
  };

  const showTyping = () => {
    const article = document.createElement("article");
    article.className = "message agent-message typing-message";
    article.innerHTML = '<span class="message-avatar" aria-hidden="true">🌍</span><div class="message-content"><div class="message-bubble typing-bubble"><span class="typing-dots" aria-hidden="true"><i></i><i></i><i></i></span><span lang="ur">Plan bana raha hoon...</span></div></div>';
    messages.append(article);
    scrollToLatest();
    return article;
  };

  const downloadPdf = async (text, button) => {
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "Preparing PDF...";
    try {
      const response = await fetch("/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!response.ok) throw new Error("PDF export failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "travel-plan.pdf";
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      window.alert("Sorry, we couldn't prepare the PDF. Please try again.");
    } finally {
      button.disabled = false;
      button.textContent = originalLabel;
    }
  };

  const sendMessage = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || activeRequest) return;
    addUserMessage(trimmed);
    input.value = "";
    input.style.height = "auto";
    form.querySelector("button[type=submit]").disabled = true;
    const typing = showTyping();
    const controller = new AbortController();
    activeRequest = controller;

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, session_id: getSessionId() }),
        signal: controller.signal,
      });
      const data = await response.json();
      if (!response.ok) {
        const reply = typeof data.reply === "string"
          ? data.reply
          : typeof data.detail === "string"
            ? data.detail
            : "I couldn't complete that plan right now. Please try again.";
        addAgentMessage(reply, { isError: true });
        return;
      }
      if (activeRequest === controller) addAgentMessage(data.reply);
    } catch (error) {
      if (activeRequest === controller && error.name !== "AbortError") {
        addAgentMessage("Sorry, we couldn't connect just now. Please try again.", { isError: true });
      }
    } finally {
      typing.remove();
      if (activeRequest === controller) {
        activeRequest = null;
        form.querySelector("button[type=submit]").disabled = false;
        input.focus();
      }
    }
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value);
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  input.addEventListener("input", resizeInput);

  document.querySelectorAll(".quick-chip:not(.example-prompt-button)").forEach((chip) => {
    chip.addEventListener("click", () => sendMessage(chip.textContent.replace(/^[^\p{L}\p{N}]+/u, "")));
  });

  examplePromptButton.addEventListener("click", () => {
    input.value = examplePrompt;
    resizeInput();
    input.focus();
  });

  newTripButton.addEventListener("click", () => {
    if (activeRequest) activeRequest.abort();
    activeRequest = null;
    form.querySelector("button[type=submit]").disabled = false;
    sessionStorage.removeItem(sessionKey);
    getSessionId();
    messages.innerHTML = welcomeMessage;
    input.value = "";
    input.focus();
  });
})();
