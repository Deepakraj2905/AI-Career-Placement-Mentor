const $ = (id) => document.getElementById(id);

async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...(options.body instanceof FormData
                ? {}
                : { "Content-Type": "application/json" }),
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong.");
    }

    return data;
}

function showMessage(id, message) {
    $(id).textContent = message;
}

function showError(id, error) {
    showMessage(id, error.message || "Something went wrong.");
}

function addText(parent, tag, text, className = "") {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    parent.appendChild(element);
    return element;
}

async function loadDashboard() {
    try {
        const data = await api("/api/dashboard");
        $("readiness").textContent = data.readiness_score + "%";
        $("resume-score").textContent = data.resume_score + "/100";
        $("skill-count").textContent = data.skills_count;
        $("practice-count").textContent = data.practice_sessions;
        showMessage("dashboard-message", data.note || "");
    } catch (error) {
        showError("dashboard-message", error);
    }
}

async function loadProfile() {
    try {
        const data = await api("/api/profile");
        $("education").value = data.education || "";
        $("skills").value = data.skills || "";
        $("interests").value = data.interests || "";
        $("target-role").value = data.target_role || "Software Engineer";
    } catch (error) {
        showError("profile-message", error);
    }
}

$("save-profile").addEventListener("click", async () => {
    try {
        const data = await api("/api/profile", {
            method: "POST",
            body: JSON.stringify({
                education: $("education").value,
                skills: $("skills").value,
                interests: $("interests").value,
                target_role: $("target-role").value
            })
        });
        showMessage("profile-message", data.message);
    } catch (error) {
        showError("profile-message", error);
    }
});

$("analyze-resume").addEventListener("click", async () => {
    const file = $("resume-file").files[0];

    if (!file) {
        showMessage("resume-results", "Please select your resume first.");
        return;
    }

    const form = new FormData();
    form.append("resume", file);
    showMessage("resume-results", "Analyzing your resume...");

    try {
        const data = await api("/api/resume", {
            method: "POST",
            body: form
        });

        const box = $("resume-results");
        box.replaceChildren();
        addText(box, "h3", "Resume Analysis");
        addText(box, "p", "Resume: " + data.filename);
        addText(box, "p", "Score: " + data.score + "/100");
        addText(box, "h4", "Skills identified");

        addText(
            box,
            "p",
            data.skills.length ? data.skills.join(", ") : "No matching skills found."
        );

        addText(box, "h4", "Suggestions");
        const list = document.createElement("ul");
        data.suggestions.forEach(item => addText(list, "li", item));
        box.appendChild(list);
        addText(box, "p", data.note);
        loadDashboard();
    } catch (error) {
        showError("resume-results", error);
    }
});

$("find-careers").addEventListener("click", async () => {
    const box = $("career-results");
    box.replaceChildren();
    addText(box, "p", "Finding suitable career roles...");

    try {
        const data = await api("/api/recommend", {
            method: "POST",
            body: JSON.stringify({
                skills: $("skills").value,
                interests: $("interests").value
            })
        });

        box.replaceChildren();

        data.recommendations.forEach(role => {
            const card = document.createElement("article");
            card.className = "result";
            addText(card, "h3", role.role);
            addText(card, "p", "Skill match: " + role.match_score + "%");
            addText(
                card,
                "p",
                "Matched skills: " + (role.matched_skills.join(", ") || "None yet")
            );
            addText(
                card,
                "p",
                "Skills to learn: " + (role.missing_skills.join(", ") || "Review your skills")
            );
            box.appendChild(card);
        });
    } catch (error) {
        showError("career-results", error);
    }
});

$("create-roadmap").addEventListener("click", async () => {
    const list = $("roadmap-results");
    list.replaceChildren();
    addText(list, "li", "Preparing your roadmap...");

    try {
        const data = await api("/api/roadmap", {
            method: "POST",
            body: JSON.stringify({
                role: $("roadmap-role").value,
                skills: $("skills").value
            })
        });

        list.replaceChildren();
        data.roadmap.forEach(step => addText(list, "li", step));
    } catch (error) {
        list.replaceChildren();
        addText(list, "li", error.message);
    }
});

$("send-chat").addEventListener("click", async () => {
    const message = $("chat-message").value.trim();

    if (!message) {
        showMessage("chat-results", "Please type a question.");
        return;
    }

    showMessage("chat-results", "Thinking...");

    try {
        const data = await api("/api/chat", {
            method: "POST",
            body: JSON.stringify({ message })
        });
        showMessage(
            "chat-results",
            data.answer + (data.ai_connected ? "" : "\n\nAI service is not connected.")
        );
    } catch (error) {
        showError("chat-results", error);
    }
});

$("submit-interview").addEventListener("click", async () => {
    const question = $("interview-question").value.trim();
    const answer = $("interview-answer").value.trim();

    if (!question || !answer) {
        showMessage("interview-results", "Enter both the question and your answer.");
        return;
    }

    showMessage("interview-results", "Preparing feedback...");

    try {
        const data = await api("/api/interview", {
            method: "POST",
            body: JSON.stringify({
                role: $("interview-role").value,
                question,
                answer
            })
        });
        showMessage("interview-results", data.feedback);
        loadDashboard();
    } catch (error) {
        showError("interview-results", error);
    }
});

loadDashboard();
loadProfile();
