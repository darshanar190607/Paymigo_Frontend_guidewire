import React, { useState, useRef, useEffect } from 'react';
import './AssistantPanel.css';
import { chatWithMigo } from '../services/chatApi';

const AssistantPanel = () => {
    const [messages, setMessages] = useState([
        { 
            role: 'migo', 
            content: "Hi! I'm Migo 👋 I can help you with claims, plans, and payouts. What would you like to explore?",
            suggestions: ["Check claim", "Best plan", "Is it safe today?"]
        }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e, customText = null) => {
        e?.preventDefault();
        const textToSend = customText || input;
        if (!textToSend.trim()) return;

        const userMsg = { role: 'user', content: textToSend };
        setMessages(prev => [...prev.map(m => ({ ...m, suggestions: [] })), userMsg]);
        setInput('');
        
        // Add artificial delay for "Thinking AI" feel
        setTimeout(async () => {
            setIsTyping(true);
            const response = await chatWithMigo(textToSend, messages);
            setIsTyping(false);
            
            const migoMsg = { 
                role: 'migo', 
                content: response.answer,
                actions: response.actions,
                suggestions: response.suggestions || []
            };
            setMessages(prev => [...prev, migoMsg]);

            if (window.speechSynthesis) {
                const utterance = new SpeechSynthesisUtterance(response.answer);
                utterance.rate = 1.1;
                window.speechSynthesis.speak(utterance);
            }
        }, 800);
    };

    const toggleVoice = () => {
        setIsListening(!isListening);
        if (!isListening) {
            console.log("Listening...");
            setTimeout(() => {
                setIsListening(false);
                handleSend(null, "How does the best plan work?");
            }, 2000);
        }
    };

    return (
        <div className="migo-container">
            <div className="migo-header">
                <h3>Migo Assistant</h3>
                <button className="voice-btn" onClick={() => setMessages([])} title="Clear Chat">
                    🔄
                </button>
            </div>
            
            <div className="migo-messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message-group ${msg.role}`}>
                        <div className={`message ${msg.role}`}>
                            {msg.content}
                        </div>
                        
                        {msg.actions && msg.actions.length > 0 && (
                            <div className="action-row">
                                {msg.actions.map((action, aIdx) => (
                                    <button 
                                        key={aIdx} 
                                        className="action-card"
                                        onClick={() => window.open(action.target, '_self')}
                                    >
                                        {action.label} →
                                    </button>
                                ))}
                            </div>
                        )}

                        {msg.suggestions && msg.suggestions.length > 0 && (
                            <div className="suggestion-row">
                                {msg.suggestions.map((s, sIdx) => (
                                    <button 
                                        key={sIdx} 
                                        className="suggestion-chip"
                                        onClick={() => handleSend(null, s)}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
                
                {isTyping && (
                    <div className="message-group migo">
                        <div className="message migo typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="migo-input-area" onSubmit={handleSend}>
                <button 
                    type="button" 
                    className={`voice-btn ${isListening ? 'active' : ''}`}
                    onClick={toggleVoice}
                >
                    🎤
                </button>
                <input 
                    className="migo-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask Migo anything..."
                />
                <button type="submit" className="voice-btn">
                    🚀
                </button>
            </form>
        </div>
    );
};

export default AssistantPanel;
