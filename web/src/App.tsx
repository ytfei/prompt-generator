import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import History from './pages/History'
import Studio from './pages/Studio'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <header>
          <h1>
            提示词<em>工坊</em>
          </h1>
          <nav className="nav">
            <Link to="/">工作台</Link>
            <Link to="/history">历史记录</Link>
          </nav>
          <span className="tag">P1 · React + FastAPI + LangGraph</span>
          <p className="sub">选配置 → 写主题 → Agent 生成优化 → 复制到「即梦」生图。</p>
        </header>
        <Routes>
          <Route path="/" element={<Studio />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
