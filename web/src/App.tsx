import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import History from './pages/History'
import Img2Img from './pages/Img2Img'
import Studio from './pages/Studio'
import Templates from './pages/Templates'

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
            <NavLink to="/history">历史记录</NavLink>
            <NavLink to="/templates">我的模板</NavLink>
          </nav>
          <p className="sub">
            文生图：选配置 → 写主题 → Agent 生成；图生图：描述已有图片 + 修改/创意意向 →
            复制到「即梦」。
          </p>
          <div className="tab-bar">
            <NavLink to="/" end className={({ isActive }) => `tab-btn${isActive ? ' on' : ''}`}>
              ✍️ 文生图
            </NavLink>
            <NavLink to="/i2i" className={({ isActive }) => `tab-btn${isActive ? ' on' : ''}`}>
              🖼️ 图生图 <span className="beta">新</span>
            </NavLink>
          </div>
        </header>
        <Routes>
          <Route path="/" element={<Studio />} />
          <Route path="/i2i" element={<Img2Img />} />
          <Route path="/history" element={<History />} />
          <Route path="/templates" element={<Templates />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
