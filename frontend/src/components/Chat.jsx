import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { sendMessage, submitFeedback } from '../services/api'

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [ratedMsgs, setRatedMsgs] = useState(new Set())
  const [toast, setToast] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const showToast = (text) => {
    setToast(text)
    setTimeout(() => setToast(null), 3000)
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const data = await sendMessage(text)
      setMessages(prev => [...prev, {
        role: 'bot',
        content: data.response,
        tools: data.tools_used || [],
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'bot',
        content: 'Sorry, I couldn\'t process your request. Please try again.',
        tools: [],
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleRate = async (msgIndex, stars) => {
    try {
      await submitFeedback({
        rating: stars,
        comment: `Quick rating on message #${msgIndex}`,
        suggestion: '',
      })
      setRatedMsgs(prev => new Set(prev).add(msgIndex))
      showToast(`Thanks! Rated ${stars}/5`)
    } catch {
      showToast('Failed to submit rating')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <span className="icon">?</span>
            <p>Ask me about crypto prices, B3 stocks, financial concepts, or investment strategies!</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-bubble">
              {msg.role === 'bot' ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>

            {msg.role === 'bot' && msg.tools?.length > 0 && (
              <div className="tool-badges">
                {msg.tools.map((t, j) => (
                  <span key={j} className="tool-badge">{t.tool_name}</span>
                ))}
              </div>
            )}

            {msg.role === 'bot' && !ratedMsgs.has(i) && (
              <div className="inline-stars">
                {[1, 2, 3, 4, 5].map(star => (
                  <button
                    key={star}
                    className="star-btn"
                    onClick={() => handleRate(i, star)}
                    title={`Rate ${star}/5`}
                  >
                    ★
                  </button>
                ))}
              </div>
            )}

            {msg.role === 'bot' && ratedMsgs.has(i) && (
              <div style={{ fontSize: '0.78rem', color: 'var(--accent-green)', marginTop: 6 }}>
                Rated
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="typing-indicator">
            <span /><span /><span />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about crypto, stocks, finance..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          {loading ? '...' : '→'} Send
        </button>
      </div>

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
