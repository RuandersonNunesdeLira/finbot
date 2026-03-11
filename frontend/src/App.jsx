import { useState, useEffect } from 'react'
import { checkHealth } from './services/api'
import Chat from './components/Chat'
import PromptManager from './components/PromptManager'
import WhatsAppSync from './components/WhatsAppSync'

const TABS = [
  { id: 'chat', label: 'Chat', icon: null },
  { id: 'prompt', label: 'Prompt & Feedback', icon: null },
  { id: 'whatsapp', label: 'WhatsApp', icon: null },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [online, setOnline] = useState(false)

  useEffect(() => {
    const check = async () => {
      try {
        await checkHealth()
        setOnline(true)
      } catch {
        setOnline(false)
      }
    }
    check()
    const interval = setInterval(check, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="logo-icon">$</span>
          <div>
            <h1>FinBot</h1>
            <div className="subtitle">AI Financial Assistant</div>
          </div>
        </div>

        <div className="sidebar-status">
          <span className={`status-dot ${online ? 'online' : 'offline'}`} />
          Backend: {online ? 'Online' : 'Offline'}
        </div>

        <div className="sidebar-section">
          <h3>Tech Stack</h3>
          <div className="sidebar-tech">
            <span>OpenAI (GPT-4o-mini)</span>
            <span>ChromaDB (Vector Store)</span>
            <span>CoinGecko (Crypto)</span>
            <span>Brapi (B3 Stocks)</span>
            <span>WAHA (WhatsApp)</span>
            <span>FastAPI + Vite</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <div className="tabs-header">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="tab-content">
          {activeTab === 'chat' && <Chat />}
          {activeTab === 'prompt' && <PromptManager />}
          {activeTab === 'whatsapp' && <WhatsAppSync />}
        </div>
      </main>
    </div>
  )
}
