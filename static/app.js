"use strict";

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

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || data.message || "Request failed");
    }

    return data;
}

function showResult(id, data) {
    const element = $(id);
    if (!element) return;

    element.replaceChildren();

    const pre = document.createElement("pre");
    pre.style.whiteSpace = "pre-wrap";
    pre.style.overflowWrap = "anywhere";
    pre.textContent = typeof data === "string"
        ? data
        : JSON.stringify(data, null, 2);

    element.appendChild(pre);
}

function showError(id, error) {
    showResult(id, "Error: " + error.message);
}

function postJSON(url, data) {
    return api(url, {
        method: "POST",
        body: JSON.stringify(data)
    });
}

async function loadDashboard() {
    try {
        const data = await api("/api/dashboard");
        showResult("dashboardResult", data);
    } catch (error) {
        showError("dashboardResult", error);
    }
}

async function saveProfile(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const profile = Object.fromEntries(new FormData(form).entries());

    try {
        const result = await postJSON("/api/profile", profile);
        showResult("profileResult", result);
    } catch (error) {
        showError("profileResult", error);
    }
}

async function uploadResume(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const formData = new FormData(form);

    try {
        const result = await api("/api/resume", {
            method: "POST",
            body: formData
        });
        showResult("resumeResult", result);
    } catch (error) {
        showError("resumeResult", error);
    }
}

async function recommendCareers(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
        const result = await postJSON("/api/recommend", data);
        showResult("recommendResult", result);
    } catch (error) {
        showError("recommendResult", error);
    }
}

async function generateRoadmap(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
        const result = await postJSON("/api/roadmap", data);
        showResult("roadmapResult", result);
    } catch (error) {
        showError("roadmapResult", error);
    }
}

async function sendChat(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
        const result = await postJSON("/api/chat", data);
        showResult("chatResult", result);
    } catch (error) {
        showError("chatResult", error);
    }
}

async function startInterview(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
        const result = await postJSON("/api/interview", data);
        showResult("interviewResult", result);
    } catch (error) {
        showError("interviewResult", error);
    }
}

function connectForm(ids, handler) {
    for (const id of ids) {
        const element = $(id);
        if (element && element.tagName === "FORM") {
            element.addEventListener("submit", handler);
            return;
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    connectForm(["profileForm"], saveProfile);
    connectForm(["resumeForm"], uploadResume);
    connectForm(["recommendForm", "careerForm"], recommendCareers);
    connectForm(["roadmapForm"], generateRoadmap);
    connectForm(["chatForm"], sendChat);
    connectForm(["interviewForm"], startInterview);

    const dashboardButton = $("refreshDashboard");
    if (dashboardButton) {
        dashboardButton.addEventListener("click", loadDashboard);
    }

    loadDashboard();
});
