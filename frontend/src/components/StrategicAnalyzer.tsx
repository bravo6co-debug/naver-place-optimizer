import { useState, useEffect } from 'react'
import axios from 'axios'
import './StrategicAnalyzer.css'

type AnalysisStepStatus = 'pending' | 'active' | 'completed'

interface AnalysisStep {
  id: number
  name: string
  description: string
  icon: string
  estimatedTime: number
  status: AnalysisStepStatus
}

interface KeywordMetrics {
  keyword: string
  level: number
  level_name: string
  estimated_monthly_searches: number
  competition_score: number
  naver_result_count: number
  difficulty_score: number
  recommended_rank_target: string
  estimated_timeline: string
  estimated_daily_traffic: number
  conversion_rate: number
  confidence: string
}

interface StrategyPhase {
  phase: number
  name: string
  duration: string
  target_level: number
  target_level_name: string
  target_keywords_count: number
  strategies: string[]
  goals: string[]
  expected_daily_visitors: number
  // V4 추가 필드
  priority_keywords: string[]
  keyword_traffic_breakdown: Record<string, number>
  difficulty_level: string
  cumulative_visitors: number
  // V5 Simplified
  receipt_review_target?: number
  weekly_review_target?: number
  consistency_importance?: string
  receipt_review_keywords?: string[]
  review_quality_standard?: {
    min_text_length: number
    min_photos: number
    keyword_count: number
    must_include_receipt_photo?: boolean
  }
  review_incentive_plan?: string
  keyword_mention_strategy?: {
    frequency: string
    placement: string
    natural_tip: string
    example: string
  }
  info_trust_checklist?: string[]
  review_templates?: {
    short: string
    medium: string
    long: string
  }
}

interface AnalysisResult {
  business_info: {
    type: string
    location: string
    specialty: string
  }
  total_keywords: number
  keywords_by_level: {
    level_5: KeywordMetrics[]
    level_4: KeywordMetrics[]
    level_3: KeywordMetrics[]
    level_2: KeywordMetrics[]
    level_1: KeywordMetrics[]
  }
  strategy_roadmap: StrategyPhase[]
  summary: {
    current_daily_visitors: number
    target_daily_visitors: number
    gap: number
    total_expected_traffic: number
    achievement_rate: number
    total_phases: number
    recommended_timeline: string
    data_sources: string[]
  }
}

// 업종 예시 (placeholder용)
const BUSINESS_TYPE_EXAMPLES = '음식점, 카페, 미용실, 병원, 학원, 헬스장, 네일샵, 편의점, 부동산 등'

const INITIAL_ANALYSIS_STEPS: AnalysisStep[] = [
  {
    id: 1,
    name: '키워드 생성',
    description: 'GPT-4로 전략적 키워드 생성 중',
    icon: '🤖',
    estimatedTime: 10,
    status: 'pending'
  },
  {
    id: 2,
    name: '검색량 분석',
    description: '네이버 검색광고 API로 실제 검색량 조회',
    icon: '📊',
    estimatedTime: 15,
    status: 'pending'
  },
  {
    id: 3,
    name: '경쟁도 측정',
    description: '35개 키워드 경쟁도 분석 중',
    icon: '🎯',
    estimatedTime: 20,
    status: 'pending'
  },
  {
    id: 4,
    name: '전략 수립',
    description: '4단계 로드맵 생성 중',
    icon: '🗺️',
    estimatedTime: 5,
    status: 'pending'
  },
  {
    id: 5,
    name: '결과 정리',
    description: '최종 분석 결과 생성',
    icon: '✨',
    estimatedTime: 3,
    status: 'pending'
  }
]

function StrategicAnalyzer() {
  const [businessType, setBusinessType] = useState('')
  const [location, setLocation] = useState('')
  const [specialty, setSpecialty] = useState('')
  const [currentVisitors, setCurrentVisitors] = useState(50)
  const [targetVisitors, setTargetVisitors] = useState(200)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'keywords' | 'roadmap'>('keywords')

  // 분석 진행 상태
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>(INITIAL_ANALYSIS_STEPS)
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  // 진행 상황 시뮬레이션
  useEffect(() => {
    if (!loading) {
      // 로딩이 끝나면 초기화
      setAnalysisSteps(INITIAL_ANALYSIS_STEPS)
      setCurrentStep(0)
      setProgress(0)
      return
    }

    let stepIndex = 0
    const totalSteps = INITIAL_ANALYSIS_STEPS.length
    const stepDuration = 3000 // 각 단계당 3초

    const interval = setInterval(() => {
      if (stepIndex < totalSteps) {
        setAnalysisSteps(prev => prev.map((step, idx) => ({
          ...step,
          status: idx < stepIndex ? 'completed' :
                  idx === stepIndex ? 'active' : 'pending'
        })))

        setCurrentStep(stepIndex)
        setProgress(((stepIndex + 1) / totalSteps) * 100)

        stepIndex++
      } else {
        clearInterval(interval)
      }
    }, stepDuration)

    return () => clearInterval(interval)
  }, [loading])

  const handleAnalyze = async () => {
    if (!businessType || !businessType.trim()) {
      setError('업종을 입력해주세요')
      return
    }

    if (!location || !location.trim()) {
      setError('위치를 입력해주세요')
      return
    }

    if (!specialty || !specialty.trim()) {
      setError('특징을 입력해주세요 (예: 브런치 전문, 24시간, 한방 치료 등)')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await axios.post('/api/v2/analyze', {
        business_type: businessType.trim(),
        location: location.trim(),
        specialty: specialty.trim() || null,
        current_daily_visitors: currentVisitors,
        target_daily_visitors: targetVisitors
      })
      setResult(response.data)
      setActiveTab('keywords')
    } catch (err: any) {
      setError(err.response?.data?.detail || '분석 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const getLevelColor = (level: number) => {
    const colors: Record<number, string> = {
      5: '#10b981', // 녹색
      4: '#3b82f6', // 파랑
      3: '#f59e0b', // 주황
      2: '#ef4444', // 빨강
      1: '#8b5cf6'  // 보라
    }
    return colors[level] || '#666'
  }

  const getLevelIcon = (level: number) => {
    const icons: Record<number, string> = {
      5: '🎯',
      4: '📍',
      3: '⚡',
      2: '🔥',
      1: '👑'
    }
    return icons[level] || '📌'
  }

  return (
    <div className="strategic-analyzer">
      <div className="analyzer-header">
        <h2>🚀 전략적 키워드 분석</h2>
        <p className="description">
          5단계 난이도 분석으로 롱테일 키워드부터 정복하여 목표 트래픽을 달성하세요
        </p>
      </div>

      <div className="input-section">
        <div className="input-row">
          <div className="input-group">
            <label>업종</label>
            <input
              type="text"
              value={businessType}
              onChange={(e) => setBusinessType(e.target.value)}
              placeholder={`예: ${BUSINESS_TYPE_EXAMPLES}`}
              disabled={loading}
            />
          </div>

          <div className="input-group">
            <label>위치</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="서울 강남구"
              disabled={loading}
            />
          </div>

          <div className="input-group">
            <label>특징 <span className="required">*</span></label>
            <input
              type="text"
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              placeholder="온천, 찜질, 인피니티풀 (컴마로 여러 개 입력 가능)"
              disabled={loading}
              required
            />
            <small style={{ color: '#666', fontSize: '0.85em', marginTop: '-2px' }}>
              💡 여러 특징을 컴마(,)로 구분하여 입력하세요
            </small>
          </div>
        </div>

        <div className="input-row">
          <div className="input-group">
            <label>현재 일방문자</label>
            <input
              type="number"
              value={currentVisitors}
              onChange={(e) => setCurrentVisitors(Number(e.target.value))}
              disabled={loading}
            />
          </div>

          <div className="input-group">
            <label>목표 일방문자</label>
            <input
              type="number"
              value={targetVisitors}
              onChange={(e) => setTargetVisitors(Number(e.target.value))}
              disabled={loading}
            />
          </div>

          <div className="input-group">
            <label>&nbsp;</label>
            <button
              className="analyze-btn"
              onClick={handleAnalyze}
              disabled={loading}
            >
              {loading ? '⏳ 분석 중...' : '🔍 전략 분석 시작'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div className="analysis-progress">
          <div className="progress-header">
            <h3>🔍 분석 진행 중...</h3>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="progress-text">{Math.round(progress)}% 완료</p>
          </div>

          <div className="steps-container">
            {analysisSteps.map((step) => (
              <div
                key={step.id}
                className={`step-item ${step.status}`}
              >
                <div className="step-icon">
                  {step.status === 'completed' ? '✅' :
                   step.status === 'active' ? step.icon : '⏳'}
                </div>
                <div className="step-content">
                  <div className="step-name">{step.name}</div>
                  <div className="step-description">
                    {step.description}
                  </div>
                </div>
                {step.status === 'active' && (
                  <div className="step-spinner">
                    <div className="spinner" />
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="progress-footer">
            <p>💡 AI가 35개의 전략적 키워드를 분석하고 있습니다</p>
            <p>⏱️ 예상 소요 시간: 약 50초</p>
          </div>
        </div>
      )}

      {result && (
        <div className="result-container">
          {/* 요약 대시보드 */}
          <div className="summary-dashboard">
            <div className="summary-card">
              <div className="summary-label">총 키워드</div>
              <div className="summary-value">{result.total_keywords}개</div>
            </div>
            <div className="summary-card">
              <div className="summary-label">필요 트래픽</div>
              <div className="summary-value">+{result.summary.gap}명/일</div>
            </div>
            <div className="summary-card">
              <div className="summary-label">권장 기간</div>
              <div className="summary-value">{result.summary.recommended_timeline}</div>
            </div>
          </div>

          {/* 탭 */}
          <div className="result-tabs">
            <button
              className={activeTab === 'keywords' ? 'active' : ''}
              onClick={() => setActiveTab('keywords')}
            >
              📊 5단계 키워드 분석
            </button>
            <button
              className={activeTab === 'roadmap' ? 'active' : ''}
              onClick={() => setActiveTab('roadmap')}
            >
              🗺️ 전략 로드맵
            </button>
          </div>

          {/* 키워드 분석 탭 */}
          {activeTab === 'keywords' && (
            <div className="keywords-tab">
              {[5, 4, 3, 2, 1].map(level => {
                const levelKey = `level_${level}` as keyof typeof result.keywords_by_level
                const keywords = result.keywords_by_level[levelKey]

                if (keywords.length === 0) return null

                return (
                  <div key={level} className="level-section">
                    <div className="level-header" style={{ borderLeftColor: getLevelColor(level) }}>
                      <span className="level-icon">{getLevelIcon(level)}</span>
                      <span className="level-title">Level {level}: {keywords[0].level_name}</span>
                      <span className="level-count">{keywords.length}개</span>
                    </div>

                    <div className="keywords-grid">
                      {keywords.map((kw, idx) => (
                        <div key={idx} className="keyword-card">
                          <div className="keyword-header">
                            <h4>{kw.keyword}</h4>
                          </div>

                          <div className="keyword-metrics">
                            <div className="metric">
                              <span className="metric-label">검색량</span>
                              <span className="metric-value">{kw.estimated_monthly_searches.toLocaleString()}/월</span>
                            </div>
                            <div className="metric">
                              <span className="metric-label">경쟁도</span>
                              <span className="metric-value">{kw.competition_score}/100</span>
                            </div>
                            <div className="metric">
                              <span className="metric-label">난이도</span>
                              <span className="metric-value">{kw.difficulty_score}/100</span>
                            </div>
                            <div className="metric">
                              <span className="metric-label">네이버 결과</span>
                              <span className="metric-value">{kw.naver_result_count.toLocaleString()}건</span>
                            </div>
                          </div>

                          <div className="keyword-target">
                            <div className="target-rank">
                              목표: <strong>{kw.recommended_rank_target}</strong>
                            </div>
                            <div className="target-timeline">
                              기간: <strong>{kw.estimated_timeline}</strong>
                            </div>
                            {kw.estimated_daily_traffic > 0 && (
                              <div className="target-traffic">
                                예상: <strong>+{kw.estimated_daily_traffic}명/일</strong>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* 전략 로드맵 탭 */}
          {activeTab === 'roadmap' && (
            <div className="roadmap-tab">
              <div className="roadmap-intro">
                <h3>📍 단계별 실행 전략</h3>
                <p>롱테일 키워드부터 시작하여 점진적으로 상위 키워드를 공략하는 전략입니다</p>
              </div>

              <div className="phases-container">
                {result.strategy_roadmap.map((phase, idx) => (
                  <div key={idx} className="phase-card">
                    <div className="phase-header">
                      <div className="phase-number">Phase {phase.phase}</div>
                      <div className="phase-info">
                        <h3>{phase.name}</h3>
                        <span className="phase-duration">{phase.duration}</span>
                      </div>
                    </div>

                    <div className="phase-target">
                      <div className="target-item">
                        <span className="target-label">타겟 레벨:</span>
                        <span className="target-value" style={{ color: getLevelColor(phase.target_level) }}>
                          {getLevelIcon(phase.target_level)} Level {phase.target_level}
                        </span>
                      </div>
                      <div className="target-item">
                        <span className="target-label">목표 키워드:</span>
                        <span className="target-value">{phase.target_keywords_count}개</span>
                      </div>
                      <div className="target-item">
                        <span className="target-label">난이도:</span>
                        <span className="target-value" style={{
                          color: phase.difficulty_level === '쉬움' ? '#10b981' :
                                 phase.difficulty_level === '보통' ? '#f59e0b' : '#ef4444'
                        }}>
                          {phase.difficulty_level}
                        </span>
                      </div>
                    </div>

                    {phase.priority_keywords && phase.priority_keywords.length > 0 && (
                      <div className="priority-keywords-section">
                        <h4>🔥 우선 공략 키워드 Top 5</h4>
                        <div className="priority-keywords">
                          {phase.priority_keywords.map((keyword, kidx) => (
                            <span key={kidx} className="priority-keyword">
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="phase-content">
                      <div className="content-section">
                        <h4>📋 실행 전략</h4>
                        <ul>
                          {phase.strategies.map((strategy, sidx) => (
                            <li key={sidx}>{strategy}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="content-section">
                        <h4>🎯 목표</h4>
                        <ul>
                          {phase.goals.map((goal, gidx) => (
                            <li key={gidx}>{goal}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {phase.receipt_review_target && phase.receipt_review_target > 0 && (
                      <div className="receipt-review-strategy-v5">
                        <h4>🎯 핵심 전략: 영수증 리뷰 + 키워드 (60%)</h4>

                        <div className="review-targets">
                          <div className="target-item">
                            <span className="label">목표:</span>
                            <span className="value primary">{phase.receipt_review_target}개</span>
                          </div>
                          <div className="target-item">
                            <span className="label">주간 목표:</span>
                            <span className="value secondary">{phase.weekly_review_target}개</span>
                          </div>
                        </div>

                        {phase.consistency_importance && (
                          <div className="consistency-warning">
                            <span className="icon">⚠️</span>
                            <span className="message">{phase.consistency_importance}</span>
                          </div>
                        )}

                        {phase.receipt_review_keywords && phase.receipt_review_keywords.length > 0 && (
                          <div className="review-keywords-section">
                            <h5>✅ 삽입할 키워드 (우선순위):</h5>
                            <div className="keyword-chips">
                              {phase.receipt_review_keywords.map((kw, idx) => (
                                <span key={idx} className={`keyword-chip priority-${idx + 1}`}>
                                  {kw}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {phase.keyword_mention_strategy && (
                          <div className="keyword-mention-guide">
                            <h5>📝 키워드 삽입 방법:</h5>
                            <ul>
                              <li><strong>빈도:</strong> {phase.keyword_mention_strategy.frequency}</li>
                              <li><strong>배치:</strong> {phase.keyword_mention_strategy.placement}</li>
                              <li><strong>팁:</strong> {phase.keyword_mention_strategy.natural_tip}</li>
                              <li><strong>예시:</strong> "{phase.keyword_mention_strategy.example}"</li>
                            </ul>
                          </div>
                        )}

                        {phase.review_quality_standard && (
                          <div className="review-quality">
                            <h5>✅ 리뷰 품질 기준 (AI 평가 통과):</h5>
                            <ul>
                              <li>텍스트: 최소 {phase.review_quality_standard.min_text_length}자</li>
                              <li>사진: 최소 {phase.review_quality_standard.min_photos}장 (영수증 포함 필수)</li>
                              <li>키워드: {phase.review_quality_standard.keyword_count}개 이상 자연스럽게</li>
                            </ul>
                          </div>
                        )}

                        {phase.review_incentive_plan && (
                          <div className="review-incentive">
                            <h5>🎁 리뷰 유도 이벤트:</h5>
                            <p>{phase.review_incentive_plan}</p>
                          </div>
                        )}

                        {phase.review_templates && (
                          <div className="review-templates-v5">
                            <h5>📄 영수증 리뷰 작성 예시 (키워드 삽입 버전):</h5>
                            <div className="template-tabs">
                              <div className="template-item">
                                <div className="template-header">짧은 리뷰 (50자)</div>
                                <pre className="template-content">{phase.review_templates.short}</pre>
                              </div>
                              <div className="template-item">
                                <div className="template-header">중간 리뷰 (100자)</div>
                                <pre className="template-content">{phase.review_templates.medium}</pre>
                              </div>
                              <div className="template-item highlight">
                                <div className="template-header">긴 리뷰 (200자+, 추천)</div>
                                <pre className="template-content">{phase.review_templates.long}</pre>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {phase.info_trust_checklist && phase.info_trust_checklist.length > 0 && (
                      <div className="info-trust-strategy">
                        <h4>📌 보조 전략: 정보 신뢰도 (30%)</h4>
                        <ul>
                          {phase.info_trust_checklist.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {idx < result.strategy_roadmap.length - 1 && (
                      <div className="phase-arrow">⬇</div>
                    )}
                  </div>
                ))}
              </div>

              <div className="roadmap-footer">
                <h4>📊 데이터 출처</h4>
                <ul>
                  {result.summary.data_sources.map((source, idx) => (
                    <li key={idx}>✓ {source}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default StrategicAnalyzer
