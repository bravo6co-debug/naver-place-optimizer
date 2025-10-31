import { useState } from 'react'
import axios from 'axios'
import './KeywordAnalyzer.css'

interface KeywordResult {
  business_info: {
    type: string
    location: string
    city: string
    district: string
  }
  competition_level: string
  keywords: {
    primary: string[]
    secondary: string[]
    longtail: string[]
  }
  recommendations: string[]
}

const BUSINESS_TYPES = [
  '음식점', '카페', '미용실', '병원', '학원',
  '숙박', '헬스장', '세차', '정비소'
]

function KeywordAnalyzer() {
  const [businessType, setBusinessType] = useState('')
  const [location, setLocation] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<KeywordResult | null>(null)
  const [error, setError] = useState('')

  const handleAnalyze = async () => {
    if (!businessType || !location) {
      setError('업종과 위치를 모두 입력해주세요')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await axios.post('/api/analyze', {
        business_type: businessType,
        location: location
      })
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || '분석 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const getCompetitionBadge = (level: string) => {
    const badges: Record<string, { text: string; color: string }> = {
      high: { text: '높음', color: '#ef4444' },
      medium: { text: '보통', color: '#f59e0b' },
      low: { text: '낮음', color: '#10b981' }
    }
    return badges[level] || badges.low
  }

  return (
    <div className="keyword-analyzer">
      <h2>📊 키워드 분석</h2>
      <p className="description">
        업종과 지역을 입력하면 최적의 키워드를 추천해드립니다
      </p>

      <div className="input-section">
        <div className="input-group">
          <label>업종</label>
          <select
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            disabled={loading}
          >
            <option value="">업종을 선택하세요</option>
            {BUSINESS_TYPES.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="input-group">
          <label>위치</label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="예: 서울 강남구, 부산 해운대"
            disabled={loading}
          />
        </div>

        <button
          className="analyze-btn"
          onClick={handleAnalyze}
          disabled={loading}
        >
          {loading ? '⏳ 분석 중...' : '🔍 분석하기'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {result && (
        <div className="result-section">
          <div className="business-info">
            <h3>📍 업체 정보</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">업종:</span>
                <span className="value">{result.business_info.type}</span>
              </div>
              <div className="info-item">
                <span className="label">위치:</span>
                <span className="value">{result.business_info.location}</span>
              </div>
              <div className="info-item">
                <span className="label">경쟁도:</span>
                <span
                  className="badge"
                  style={{
                    background: getCompetitionBadge(result.competition_level).color
                  }}
                >
                  {getCompetitionBadge(result.competition_level).text}
                </span>
              </div>
            </div>
          </div>

          <div className="keywords-section">
            <div className="keyword-group">
              <h3>🎯 주력 키워드</h3>
              <p className="keyword-desc">가장 중요한 키워드입니다</p>
              <div className="keyword-list primary">
                {result.keywords.primary.map((kw, idx) => (
                  <span key={idx} className="keyword-tag">{kw}</span>
                ))}
              </div>
            </div>

            <div className="keyword-group">
              <h3>📌 보조 키워드</h3>
              <p className="keyword-desc">추가로 타겟팅할 키워드입니다</p>
              <div className="keyword-list secondary">
                {result.keywords.secondary.map((kw, idx) => (
                  <span key={idx} className="keyword-tag">{kw}</span>
                ))}
              </div>
            </div>

            <div className="keyword-group">
              <h3>🔎 롱테일 키워드</h3>
              <p className="keyword-desc">구체적인 검색어입니다</p>
              <div className="keyword-list longtail">
                {result.keywords.longtail.map((kw, idx) => (
                  <span key={idx} className="keyword-tag">{kw}</span>
                ))}
              </div>
            </div>
          </div>

          <div className="recommendations">
            <h3>💡 추천사항</h3>
            <ul>
              {result.recommendations.map((rec, idx) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

export default KeywordAnalyzer
