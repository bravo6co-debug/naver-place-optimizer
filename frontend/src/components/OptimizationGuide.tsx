import { useState, useEffect } from 'react'
import axios from 'axios'
import './OptimizationGuide.css'

interface Guide {
  section: string
  title: string
  content: string
  priority: string
}

function OptimizationGuide() {
  const [guides, setGuides] = useState<Guide[]>([])
  const [selectedGuide, setSelectedGuide] = useState<Guide | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchGuides()
  }, [])

  const fetchGuides = async () => {
    try {
      const response = await axios.get('/api/guides')
      setGuides(response.data.guides)
      if (response.data.guides.length > 0) {
        setSelectedGuide(response.data.guides[0])
      }
    } catch (err: any) {
      setError('가이드를 불러오는 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const getPriorityBadge = (priority: string) => {
    const badges: Record<string, { text: string; color: string }> = {
      high: { text: '필수', color: '#ef4444' },
      medium: { text: '권장', color: '#f59e0b' },
      low: { text: '선택', color: '#10b981' }
    }
    return badges[priority] || badges.medium
  }

  const formatContent = (content: string) => {
    return content.split('\n').map((line, idx) => {
      if (line.startsWith('###')) {
        return <h4 key={idx} className="guide-subtitle">{line.replace('###', '').trim()}</h4>
      } else if (line.startsWith('✅') || line.startsWith('❌')) {
        return <p key={idx} className="guide-point">{line}</p>
      } else if (line.match(/^\d+\./)) {
        return <p key={idx} className="guide-list-item">{line}</p>
      } else if (line.startsWith('-')) {
        return <p key={idx} className="guide-list-item">{line}</p>
      } else if (line.trim()) {
        return <p key={idx} className="guide-text">{line}</p>
      }
      return null
    })
  }

  if (loading) {
    return (
      <div className="optimization-guide">
        <div className="loading">⏳ 가이드를 불러오는 중...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="optimization-guide">
        <div className="error-message">⚠️ {error}</div>
      </div>
    )
  }

  return (
    <div className="optimization-guide">
      <h2>📖 최적화 가이드</h2>
      <p className="description">
        네이버 플레이스 최적화를 위한 실전 가이드입니다
      </p>

      <div className="guide-container">
        <div className="guide-menu">
          {guides.map((guide) => (
            <button
              key={guide.section}
              className={`guide-menu-item ${selectedGuide?.section === guide.section ? 'active' : ''}`}
              onClick={() => setSelectedGuide(guide)}
            >
              <span className="guide-menu-title">{guide.title}</span>
              <span
                className="priority-badge"
                style={{ background: getPriorityBadge(guide.priority).color }}
              >
                {getPriorityBadge(guide.priority).text}
              </span>
            </button>
          ))}
        </div>

        <div className="guide-content">
          {selectedGuide && (
            <>
              <div className="guide-header">
                <h3>{selectedGuide.title}</h3>
                <span
                  className="priority-badge large"
                  style={{ background: getPriorityBadge(selectedGuide.priority).color }}
                >
                  {getPriorityBadge(selectedGuide.priority).text}
                </span>
              </div>
              <div className="guide-body">
                {formatContent(selectedGuide.content)}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="guide-footer">
        <div className="tips-box">
          <h4>💡 빠른 시작 팁</h4>
          <ul>
            <li><strong>필수</strong> 항목부터 완료하세요</li>
            <li>주 1회 이상 프로필을 업데이트하세요</li>
            <li>리뷰 응답률 90% 이상을 유지하세요</li>
            <li>경쟁사를 정기적으로 모니터링하세요</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default OptimizationGuide
