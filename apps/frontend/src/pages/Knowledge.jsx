import Sidebar from '../components/Sidebar'

export default function Knowledge() {
  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">知识点</h1>
          <p className="page-subtitle">系统化学科知识体系</p>
        </div>
        <div className="card empty-state">
          <p style={{ fontSize: 15, marginBottom: 8 }}>📚 知识图谱建设中</p>
          <p style={{ fontSize: 13, color: 'var(--muted)' }}>
            完整的学科知识体系将在后续版本中推出
          </p>
        </div>
      </main>
    </div>
  )
}
