const API_BASE_URL = "http://localhost:8001";

export const chatWithMigo = async (message, history = []) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ message, history }),
        });

        if (!response.ok) {
            throw new Error("Failed to communicate with Migo");
        }

        return await response.json();
    } catch (error) {
        console.error("Chat API Error:", error);
        return {
            answer: "Sorry, I'm having trouble connecting to the server. Is the backend running?",
            action: null,
        };
    }
};

export const checkHealth = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return await response.json();
    } catch (error) {
        return { status: "offline" };
    }
};
