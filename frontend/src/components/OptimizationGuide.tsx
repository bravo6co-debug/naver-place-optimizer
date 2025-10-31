import { useState, useEffect } from 'react'
import axios from 'axios'
import './OptimizationGuide.css'

interface Guide {
  section: string
  title: string
  content: string
  priority: string
}

type BusinessType = '공통' | '카페' | '음식점' | '병원' | '미용실' | '학원' | '헬스장'

interface BusinessTypeInfo {
  name: BusinessType
  icon: string
  color: string
}

const BUSINESS_TYPES: BusinessTypeInfo[] = [
  { name: '공통', icon: '🎯', color: '#6366f1' },
  { name: '카페', icon: '☕', color: '#8b5cf6' },
  { name: '음식점', icon: '🍽️', color: '#ec4899' },
  { name: '병원', icon: '🏥', color: '#ef4444' },
  { name: '미용실', icon: '✂️', color: '#f59e0b' },
  { name: '학원', icon: '📚', color: '#10b981' },
  { name: '헬스장', icon: '💪', color: '#06b6d4' }
]

function OptimizationGuide() {
  const [guides, setGuides] = useState<Guide[]>([])
  const [selectedGuide, setSelectedGuide] = useState<Guide | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedBusinessType, setSelectedBusinessType] = useState<BusinessType>('공통')

  useEffect(() => {
    fetchGuides(selectedBusinessType)
  }, [selectedBusinessType])

  const fetchGuides = async (businessType: BusinessType) => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/guides?business_type=${encodeURIComponent(businessType)}`)
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

  const handleBusinessTypeChange = (businessType: BusinessType) => {
    setSelectedBusinessType(businessType)
    setSelectedGuide(null)
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
      <h2>📖 업종별 최적화 가이드</h2>
      <p className="description">
        업종을 선택하면 맞춤형 최적화 전략을 확인할 수 있습니다
      </p>

      {/* 업종 선택 버튼 */}
      <div className="business-type-selector">
        {BUSINESS_TYPES.map((type) => (
          <button
            key={type.name}
            className={`business-type-btn ${selectedBusinessType === type.name ? 'active' : ''}`}
            onClick={() => handleBusinessTypeChange(type.name)}
            style={{
              borderColor: selectedBusinessType === type.name ? type.color : '#e5e7eb',
              background: selectedBusinessType === type.name ? `${type.color}15` : 'white'
            }}
          >
            <span className="business-type-icon">{type.icon}</span>
            <span className="business-type-name">{type.name}</span>
          </button>
        ))}
      </div>

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
