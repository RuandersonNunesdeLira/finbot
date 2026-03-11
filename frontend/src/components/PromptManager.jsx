import { useState, useEffect } from 'react'
import { getPromptStatus, submitFeedback, getFeedbacks, processOptimize } from '../services/api'

export default function PromptManager() {
  const [promptData, setPromptData] = useState(null)
  const [feedbacks, setFeedbacks] = useState([])
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [rating, setRating] = useState(3)
  const [comment, setComment] = useState('')
  const [suggestion, setSuggestion] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  const [toast, setToast] = useState(null)

  const showToast = (text) => {
    setToast(text)
    setTimeout(() => setToast(null), 3000)
  }

  const loadData = async () => {
    try {
      const [prompt, fb] = await Promise.all([getPromptStatus(), getFeedbacks()])
      setPromptData(prompt)
      setFeedbacks(fb || [])
    } catch { /* silent */ }
  }

  useEffect(() => { loadData() }, [])

  const handleSubmitFeedback = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await submitFeedback({ rating, comment, suggestion })
      showToast('Feedback submitted! Prompt optimization triggered.')
      setComment('')
      setSuggestion('')
      setRating(3)
      // Reload data after a short delay to allow the background optimization to complete
      setTimeout(loadData, 3000)
    } catch {
      showToast('Failed to submit feedback')
    } finally {
      setSubmitting(false)
    }
  }

  const handleOptimize = async () => {
    setOptimizing(true)
    try {
      const result = await processOptimize()
      if (result.status === 'updated') {
        showToast(`Prompt updated to v${result.new_version}!`)
        loadData()
      } else {
        showToast('No changes needed based on current feedback.')
      }
    } catch {
      showToast('Optimization failed')
    } finally {
      setOptimizing(false)
    }
  }

  // Determine which prompt text to display
  const displayPrompt = selectedVersion !== null
    ? promptData?.history?.find(v => v.version === selectedVersion)?.prompt_text
    : promptData?.current_prompt

  return (
    <div className="prompt-tab">
      {/* Left Column */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Current Prompt */}
        <div className="card">
          <h2>System Prompt</h2>
          {promptData && (
            <>
              <span className="version-badge">
                {selectedVersion !== null ? `v${selectedVersion}` : `v${promptData.current_version}`}
                {selectedVersion !== null && selectedVersion !== promptData.current_version && ' (old)'}
              </span>
              <div className="prompt-display">{displayPrompt}</div>
            </>
          )}
        </div>

        {/* Version History */}
        <div className="card">
          <h2>Version History</h2>
          {promptData?.history?.length > 0 ? (
            <div className="prompt-history-list">
              {[...promptData.history].reverse().map((v) => (
                <div
                  key={v.version}
                  className={`history-item ${selectedVersion === v.version ? 'active' : ''}`}
                  onClick={() => setSelectedVersion(
                    selectedVersion === v.version ? null : v.version
                  )}
                >
                  <div className="version">
                    v{v.version}
                    {v.version === promptData.current_version && (
                      <span style={{ color: 'var(--accent-green)', marginLeft: 8, fontSize: '0.75rem' }}>● current</span>
                    )}
                  </div>
                  <div className="reason">{v.reason}</div>
                  <div className="prompt-preview">{v.prompt_text?.substring(0, 100)}...</div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>No version history yet.</p>
          )}
        </div>

        {/* Auto-Optimize */}
        <div className="card">
          <h2>Auto-Optimize Prompt</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 12 }}>
            Analyzes all collected feedback and uses AI to generate an improved system prompt.
          </p>
          <button className="btn btn-primary" onClick={handleOptimize} disabled={optimizing}>
            {optimizing ? 'Optimizing...' : 'Process Feedback & Optimize'}
          </button>
        </div>
      </div>

      {/* Right Column */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Submit Feedback */}
        <div className="card">
          <h2>Submit Feedback</h2>
          <form onSubmit={handleSubmitFeedback}>
            <div className="form-group">
              <label>Rating</label>
              <div className="rating-stars">
                {[1, 2, 3, 4, 5].map(star => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    style={{ opacity: star <= rating ? 1 : 0.3 }}
                  >
                    ★
                  </button>
                ))}
                <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginLeft: 8 }}>
                  {rating}/5
                </span>
              </div>
            </div>

            <div className="form-group">
              <label>Comment</label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="How was the response quality?"
              />
            </div>

            <div className="form-group">
              <label>Suggestion for improvement</label>
              <textarea
                value={suggestion}
                onChange={(e) => setSuggestion(e.target.value)}
                placeholder="e.g., 'Be more concise', 'Add risk details'..."
              />
            </div>

            <button className="btn btn-primary" type="submit" disabled={submitting}>
              {submitting ? 'Sending...' : 'Submit Feedback'}
            </button>
          </form>
        </div>

        {/* Feedback History */}
        <div className="card">
          <h2>Feedback History</h2>
          {feedbacks.length > 0 ? (
            <div className="feedback-list">
              {[...feedbacks].reverse().slice(0, 15).map((fb, i) => (
                <div key={i} className="feedback-item">
                  <span className="stars">{'★'.repeat(fb.rating)}</span>
                  <span className="fb-status">
                    {fb.applied ? 'Applied' : 'Pending'}
                  </span>
                  {fb.comment && <div className="fb-comment">{fb.comment}</div>}
                  {fb.suggestion && <div className="fb-comment">{fb.suggestion}</div>}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
              No feedback yet. Start chatting and rate the responses!
            </p>
          )}
        </div>
      </div>

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
