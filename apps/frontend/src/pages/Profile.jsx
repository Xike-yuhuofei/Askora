import { useState, useEffect } from 'react'
import { TrendingUp, BookOpen, Target, Brain, Clock, Award } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import * as usersApi from '../api/users'
import './Profile.css'

export default function Profile() {
  const isDemoMode = localStorage.getItem('demo_mode') === 'true'
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isDemoMode) {
      setProfile({
        total_sessions: 0,
        total_learning_minutes: 0,
        streak_days: 0,
        skills_mastered: 0,
        mastery_summary: {},
        metacognition: {},
      })
      setLoading(false)
    } else {
      loadProfile()
    }
  }, [isDemoMode])

  const loadProfile = async () => {
    try {
      const data = await usersApi.getProfile()
      setProfile(data.profile)
    } catch {
      setError('学习画像加载失败，请确认后端服务和登录状态')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
            <div className="spinner" />
          </div>
        </main>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <div className="page-header">
            <h1 className="page-title">学习画像</h1>
          </div>
          <div className="card empty-text" role="alert">{error || '暂无学习画像'}</div>
        </main>
      </div>
    )
  }

  const subjects = Object.entries(profile.mastery_summary || {})
  const subjectNames = {
    math: '数学', chinese: '语文', english: '英语', physics: '物理',
    chemistry: '化学', biology: '生物', history: '历史', geography: '地理',
  }

  return (
    <div className="app-container">
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">学习画像</h1>
          <p className="page-subtitle">你的学习数据与能力画像</p>
        </div>
        {isDemoMode && (
          <div className="card empty-text" role="note">
            演示模式：以下为本地空白示例，不代表真实学习记录。
          </div>
        )}

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(37,99,235,0.1)', color: 'var(--accent)' }}>
              <BookOpen size={20} />
            </div>
            <div className="stat-number">{profile.total_sessions}</div>
            <div className="stat-label">学习会话</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(124,58,237,0.1)', color: 'var(--accent2)' }}>
              <Clock size={20} />
            </div>
            <div className="stat-number">{Math.floor(profile.total_learning_minutes / 60)}h</div>
            <div className="stat-label">学习时长</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(5,150,105,0.1)', color: 'var(--success)' }}>
              <TrendingUp size={20} />
            </div>
            <div className="stat-number">{profile.streak_days}</div>
            <div className="stat-label">连续学习天数</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(217,119,6,0.1)', color: 'var(--warning)' }}>
              <Award size={20} />
            </div>
            <div className="stat-number">{profile.skills_mastered}</div>
            <div className="stat-label">掌握知识点</div>
          </div>
        </div>

        <div className="profile-grid">
          <div className="card profile-card">
            <div className="card-header">
              <Target size={18} />
              <h3>学科掌握度</h3>
            </div>
            <div className="mastery-list">
              {subjects.length === 0 && <p className="empty-text">完成学习会话后，这里会显示掌握度。</p>}
              {subjects.map(([key, data]) => (
                <div key={key} className="mastery-item">
                  <div className="mastery-label">
                    <span>{subjectNames[key] || key}</span>
                    <span className="mastery-count">{data.mastered_count}/{data.kp_count}</span>
                  </div>
                  <div className="mastery-bar">
                    <div
                      className="mastery-fill"
                      style={{
                        width: `${(data.mastery * 100).toFixed(0)}%`,
                        background: data.mastery > 0.6
                          ? 'linear-gradient(90deg, var(--success), #10b981)'
                          : data.mastery > 0.4
                            ? 'linear-gradient(90deg, var(--warning), #f59e0b)'
                            : 'linear-gradient(90deg, var(--danger), #ef4444)',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card profile-card">
            <div className="card-header">
              <Brain size={18} />
              <h3>元认知能力</h3>
            </div>
            <div className="metacognition-grid">
              {Object.keys(profile.metacognition || {}).length === 0 && (
                <p className="empty-text">暂无足够数据生成元认知评估。</p>
              )}
              {Object.entries(profile.metacognition || {}).map(([key, value]) => (
                <div key={key} className="meta-item">
                  <div className="meta-ring">
                    <svg viewBox="0 0 60 60">
                      <circle cx="30" cy="30" r="26" fill="none" stroke="var(--rule)" strokeWidth="5" />
                      <circle
                        cx="30" cy="30" r="26" fill="none"
                        stroke="url(#metaGrad)" strokeWidth="5"
                        strokeDasharray={`${value * 163.4} 163.4`}
                        strokeLinecap="round"
                        transform="rotate(-90 30 30)"
                      />
                      <defs>
                        <linearGradient id="metaGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="var(--accent)" />
                          <stop offset="100%" stopColor="var(--accent2)" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <span className="meta-value">{Math.round(value * 100)}%</span>
                  </div>
                  <div className="meta-label">
                    {{
                      planning_ability: '规划能力',
                      monitoring_ability: '监控能力',
                      evaluation_ability: '评价能力',
                      reflection_quality: '反思质量',
                    }[key] || key}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card profile-card full-width">
            <div className="card-header">
              <TrendingUp size={18} />
              <h3>学习建议</h3>
            </div>
            <div className="suggestions">
              <div className="suggestion-item">
                <span className="suggestion-tag tag-info">建议</span>
                <p>继续完成对话和练习；积累足够数据后，系统会在这里生成个性化建议。</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
