import Alert from '../components/ui/Alert'

export default function CourseCreate() {
  return (
    <section className="surface page-stack" aria-labelledby="course-create-title">
      <header className="page-header">
        <p className="eyebrow">课程</p>
        <h1 id="course-create-title">新课程</h1>
      </header>
      <Alert tone="info" title="打开此页不会创建课程">
        只有提交正式的 Workspace create command 才会产生真实课程。当前创建接口尚未接通，因此不会显示成功或占位课程。
      </Alert>
    </section>
  )
}
