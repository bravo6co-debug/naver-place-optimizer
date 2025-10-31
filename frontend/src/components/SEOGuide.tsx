import { useState, useEffect } from 'react'
import axios from 'axios'
import './SEOGuide.css'

interface SEOGuideData {
  guide: {
    [key: string]: any
  }
  version: string
  last_updated: string
}

function SEOGuide() {
  const [guideData, setGuideData] = useState<SEOGuideData | null>(null)
  const [activeSection, setActiveSection] = useState<string>('ranking_factors')
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchSEOGuide()
  }, [])

  const fetchSEOGuide = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/seo-guide')
      setGuideData(response.data)
    } catch (err: any) {
      setError('SEO 가이드를 불러오는 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const toggleCheckItem = (itemKey: string) => {
    setCheckedItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(itemKey)) {
        newSet.delete(itemKey)
      } else {
        newSet.add(itemKey)
      }
      return newSet
    })
  }

  const getSectionIcon = (section: string) => {
    const icons: Record<string, string> = {
      ranking_factors: '🎯',
      algorithm_updates: '🤖',
      optimization_checklist: '✅',
      industry_specific: '🏢'
    }
    return icons[section] || '📋'
  }

  const renderRankingFactors = (content: any) => {
    return (
      <div className="seo-section-content">
        <p className="section-intro">{content.intro}</p>
        <div className="factors-grid">
          {content.factors.map((factor: any, idx: number) => (
            <div key={idx} className="factor-card">
              <div className="factor-header">
                <span className="factor-icon">{factor.icon}</span>
                <h4>{factor.name}</h4>
              </div>
              <p className="factor-description">{factor.description}</p>
              <ul className="factor-details">
                {factor.details.map((detail: string, detailIdx: number) => (
                  <li key={detailIdx}>{detail}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderAlgorithmUpdates = (content: any) => {
    return (
      <div className="seo-section-content">
        <p className="section-intro">{content.intro}</p>
        <div className="algorithms-list">
          {content.algorithms.map((algo: any, idx: number) => (
            <div key={idx} className="algorithm-card">
              <div className="algorithm-header">
                <span className="algorithm-icon">{algo.icon}</span>
                <div>
                  <h4>{algo.name}</h4>
                  <p className="algorithm-description">{algo.description}</p>
                </div>
              </div>
              <ul className="algorithm-components">
                {algo.components.map((component: string, compIdx: number) => (
                  <li key={compIdx}>{component}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderOptimizationChecklist = (content: any) => {
    return (
      <div className="seo-section-content">
        <p className="section-intro">{content.intro}</p>
        {content.categories.map((category: any, catIdx: number) => (
          <div key={catIdx} className="checklist-category">
            <div className="category-header">
              <span className="category-icon">{category.icon}</span>
              <h4>{category.name}</h4>
            </div>
            <div className="checklist-items">
              {category.checklist.map((item: any, itemIdx: number) => {
                const itemKey = `${catIdx}-${itemIdx}`
                const isChecked = checkedItems.has(itemKey)
                return (
                  <div
                    key={itemIdx}
                    className={`checklist-item ${isChecked ? 'checked' : ''}`}
                    onClick={() => toggleCheckItem(itemKey)}
                  >
                    <div className="checkbox">
                      {isChecked && <span className="checkmark">✓</span>}
                    </div>
                    <div className="item-content">
                      <span className="item-text">{item.item}</span>
                      <span className={`priority-badge ${item.priority}`}>
                        {item.priority}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    )
  }


  const renderIndustrySpecific = (content: any) => {
    return (
      <div className="seo-section-content">
        <p className="section-intro">{content.intro}</p>
        <div className="industries-grid">
          {content.industries.map((industry: any, idx: number) => (
            <div key={idx} className="industry-card">
              <div className="industry-header">
                <span className="industry-icon">{industry.icon}</span>
                <h4>{industry.name}</h4>
              </div>

              <div className="industry-section">
                <h5>🔑 추천 키워드</h5>
                <div className="keywords-list">
                  {industry.keywords.map((keyword: string, kIdx: number) => (
                    <span key={kIdx} className="keyword-tag">{keyword}</span>
                  ))}
                </div>
              </div>

              <div className="industry-section">
                <h5>📷 사진 전략</h5>
                <ul>
                  {industry.photo_tips.map((tip: string, tIdx: number) => (
                    <li key={tIdx}>{tip}</li>
                  ))}
                </ul>
              </div>

              <div className="industry-section">
                <h5>🎯 키워드 전략</h5>
                <p>{industry.keyword_strategy}</p>
              </div>

              <div className="industry-section">
                <h5>⭐ 리뷰 포커스</h5>
                <p>{industry.review_focus}</p>
              </div>

              {industry.compliance && (
                <div className="industry-section compliance">
                  <h5>⚖️ 법률 준수</h5>
                  <p>{industry.compliance}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderSectionContent = (section: string) => {
    if (!guideData) return null

    const sectionData = guideData.guide[section]
    if (!sectionData) return null

    switch (section) {
      case 'ranking_factors':
        return renderRankingFactors(sectionData.content)
      case 'algorithm_updates':
        return renderAlgorithmUpdates(sectionData.content)
      case 'optimization_checklist':
        return renderOptimizationChecklist(sectionData.content)
      case 'industry_specific':
        return renderIndustrySpecific(sectionData.content)
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="seo-guide">
        <div className="loading">⏳ SEO 가이드를 불러오는 중...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="seo-guide">
        <div className="error-message">⚠️ {error}</div>
      </div>
    )
  }

  return (
    <div className="seo-guide">
      <div className="seo-header">
        <h2>🚀 네이버 플레이스 SEO 완벽 가이드</h2>
        <p className="seo-description">
          검색 알고리즘 분석부터 실전 최적화까지, 상위 노출을 위한 모든 전략을 확인하세요
        </p>
      </div>

      <div className="seo-nav">
        {guideData && Object.entries(guideData.guide).map(([key, value]: [string, any]) => (
          <button
            key={key}
            className={`seo-nav-btn ${activeSection === key ? 'active' : ''}`}
            onClick={() => setActiveSection(key)}
          >
            <span className="nav-icon">{getSectionIcon(key)}</span>
            <span className="nav-text">{value.title}</span>
            {value.priority === 'high' && <span className="priority-dot"></span>}
          </button>
        ))}
      </div>

      <div className="seo-content">
        {renderSectionContent(activeSection)}
      </div>

      <div className="seo-footer">
        <div className="tips-banner">
          <h4>💡 핵심 포인트</h4>
          <ul>
            <li>✅ 영수증 리뷰 확보가 2025년 최우선 전략</li>
            <li>✅ 스마트플레이스 앱으로 주 3회 이상 관리</li>
            <li>✅ 사진 20장 이상 + 월 1회 업데이트</li>
            <li>✅ 3개월 주기 관리로 순위 유지</li>
            <li>✅ 업종별 특화 전략으로 차별화</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default SEOGuide
