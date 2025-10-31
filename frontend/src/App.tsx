import { useState } from 'react'
import StrategicAnalyzer from './components/StrategicAnalyzer'
import OptimizationGuide from './components/OptimizationGuide'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'analyzer' | 'guide'>('analyzer')

  return (
    <div className="app">
      <header className="header">
        <h1>🎯 네이버 플레이스 최적화 서비스 v2.0</h1>
        <p>5단계 전략적 키워드 분석 · 롱테일부터 정복하는 트래픽 증대 로드맵</p>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'analyzer' ? 'active' : ''}
          onClick={() => setActiveTab('analyzer')}
        >
          🚀 전략적 분석
        </button>
        <button
          className={activeTab === 'guide' ? 'active' : ''}
          onClick={() => setActiveTab('guide')}
        >
          📖 최적화 가이드
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'analyzer' ? <StrategicAnalyzer /> : <OptimizationGuide />}
      </main>

      <footer className="footer">
        <p>© 2025 Bravo Six Corp. | 네이버 플레이스 최적화 v2.0.0 · Powered by GPT-4 & Naver API</p>
      </footer>
    </div>
  )
}

export default App
