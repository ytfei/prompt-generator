// 即梦页面内浮动助手：选维度 → 填主题 → 生成 → 一键复制。
// UI 挂在 shadow DOM 里，避免与页面样式互相污染；API 由 content script 直连服务端
//（服务端 CORS 已放行即梦域名），不经过 background，规避 MV3 service worker
// 空闲回收导致的长耗时 SSE 流中断问题。

const DEFAULT_SERVER = 'http://localhost:8100'
const STORAGE_KEYS = { sel: 'psxSelections', theme: 'psxTheme' }

const NODE_LABELS = {
  parse_intent: '解析主题意图',
  enrich_details: '补全画面细节',
  conflict_check: '检查并修正维度冲突',
  assemble: '汇总组装提示词',
  refine: '润色输出最终结果',
  apply_instruction: '应用修改要求',
  conflict_scan: '冲突扫描',
}
const GEN_NODES = ['parse_intent', 'enrich_details', 'conflict_check', 'assemble', 'refine']
const REFINE_NODES = ['apply_instruction', 'conflict_scan']

let settings = { serverUrl: DEFAULT_SERVER, autoActivate: true }
let optionsData = null // { groups, presets, models }
let selections = {} // Record<groupId, string | string[]>
let theme = ''
let modelTier = 'default'
let lastResult = null
let generating = false
let panelVisible = false

let ui = {} // shadow DOM 内的元素引用

// ---------- 基础工具 ----------

// 直连服务端（服务端 CORS 已放行即梦域名）。
// 不经 background 转发：MV3 service worker 会在 LLM 长耗时无事件时被 Chrome
// 空闲回收（约 30s），流式连接随之中断，表现为生成卡在最后一步不动。
async function api(path, method = 'GET', body) {
  try {
    const resp = await fetch(settings.serverUrl + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    const data = await resp.json().catch(() => null)
    return { ok: resp.ok, status: resp.status, data }
  } catch (e) {
    return { ok: false, status: 0, data: null, error: String(e) }
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.cssText = 'position:fixed;opacity:0'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    ta.remove()
    return ok
  }
}

function toast(shadow, msg) {
  const old = shadow.querySelector('.psx-toast')
  if (old) old.remove()
  const el = document.createElement('div')
  el.className = 'psx-toast'
  el.textContent = msg
  shadow.appendChild(el)
  setTimeout(() => el.remove(), 1600)
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]))
}

function selectedCount(gid) {
  const v = selections[gid]
  if (!v) return 0
  return Array.isArray(v) ? v.length : 1
}

// ---------- 初始化 ----------

async function init() {
  const stored = await chrome.storage.local.get(['serverUrl', 'autoActivate', STORAGE_KEYS.sel, STORAGE_KEYS.theme])
  settings.serverUrl = stored.serverUrl || DEFAULT_SERVER
  settings.autoActivate = stored.autoActivate !== false
  selections = stored[STORAGE_KEYS.sel] || {}
  theme = stored[STORAGE_KEYS.theme] || ''

  const host = document.createElement('div')
  host.id = 'psx-root'
  host.style.cssText = 'position:fixed;top:0;right:0;width:0;height:0;z-index:2147483647;'
  document.documentElement.appendChild(host)
  const shadow = host.attachShadow({ mode: 'open' })
  ui.shadow = shadow

  const css = await fetch(chrome.runtime.getURL('content.css')).then((r) => r.text())
  const style = document.createElement('style')
  style.textContent = css
  shadow.appendChild(style)

  buildUI()

  if (settings.autoActivate) showPanel(true)

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return
    if (changes.serverUrl) settings.serverUrl = changes.serverUrl.newValue || DEFAULT_SERVER
    if (changes.autoActivate !== undefined) {
      settings.autoActivate = changes.autoActivate.newValue !== false
      showPanel(settings.autoActivate)
    }
  })

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.type === 'psx-set-visible') {
      showPanel(msg.visible === 'toggle' ? !panelVisible : !!msg.visible)
    }
  })

  checkHealth()
}

function checkHealth() {
  ui.dot?.classList.remove('ok')
  api('/api/health').then((r) => {
    ui.dot?.classList.toggle('ok', !!r.ok)
    ui.statusTip && (ui.statusTip.textContent = r.ok ? '服务已连接' : '服务未连接')
  })
}

// ---------- UI 构建 ----------

function buildUI() {
  const shadow = ui.shadow

  const fab = document.createElement('button')
  fab.className = 'psx-fab psx-hidden'
  fab.title = '提示词工坊'
  fab.textContent = '✨'
  fab.addEventListener('click', () => showPanel(true))
  shadow.appendChild(fab)
  ui.fab = fab

  const panel = document.createElement('div')
  panel.className = 'psx-panel psx-hidden'
  panel.innerHTML = `
    <div class="psx-head">
      <span class="psx-dot" title="服务状态"></span>
      <span class="psx-head-title">提示词工坊</span>
      <button class="psx-head-btn psx-refresh" title="刷新连接">↻</button>
      <button class="psx-head-btn psx-close" title="收起">✕</button>
    </div>
    <div class="psx-tabs">
      <button class="psx-tab on" data-tab="gen">生成</button>
      <button class="psx-tab" data-tab="hist">历史</button>
    </div>
    <div class="psx-body psx-tab-gen"></div>
    <div class="psx-body psx-tab-hist psx-hidden"></div>
  `
  shadow.appendChild(panel)
  ui.panel = panel
  ui.dot = panel.querySelector('.psx-dot')

  panel.querySelector('.psx-close').addEventListener('click', () => showPanel(false))
  panel.querySelector('.psx-refresh').addEventListener('click', () => { checkHealth(); loadOptions(true) })

  panel.querySelectorAll('.psx-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      panel.querySelectorAll('.psx-tab').forEach((t) => t.classList.toggle('on', t === tab))
      panel.querySelector('.psx-tab-gen').classList.toggle('psx-hidden', tab.dataset.tab !== 'gen')
      panel.querySelector('.psx-tab-hist').classList.toggle('psx-hidden', tab.dataset.tab !== 'hist')
      if (tab.dataset.tab === 'hist') loadHistory()
    })
  })

  buildGenTab(panel.querySelector('.psx-tab-gen'))
  loadOptions()
}

function buildGenTab(root) {
  root.innerHTML = `
    <div class="psx-row">
      <select class="psx-select psx-preset" style="flex:1"><option value="">📦 应用预设…</option></select>
      <button class="psx-btn ghost psx-clear">清空</button>
    </div>
    <div class="psx-groups"></div>
    <div class="psx-row" style="margin-top:10px;align-items:flex-start">
      <textarea class="psx-textarea psx-theme" placeholder="主题描述（可留空，如：一杯冒着热气的咖啡）"></textarea>
    </div>
    <div class="psx-suggest psx-theme-suggest psx-hidden"></div>
    <div class="psx-row" style="margin-top:10px">
      <select class="psx-select psx-tier" style="flex:1"><option value="default">模型：默认</option></select>
      <button class="psx-btn psx-inspire">🎲 灵感</button>
      <button class="psx-btn primary psx-generate">生成提示词</button>
    </div>
    <div class="psx-steps"></div>
    <div class="psx-result-wrap"></div>
  `
  ui.groups = root.querySelector('.psx-groups')
  ui.presetSel = root.querySelector('.psx-preset')
  ui.tierSel = root.querySelector('.psx-tier')
  ui.themeTa = root.querySelector('.psx-theme')
  ui.themeSuggest = root.querySelector('.psx-theme-suggest')
  ui.steps = root.querySelector('.psx-steps')
  ui.resultWrap = root.querySelector('.psx-result-wrap')

  ui.themeTa.value = theme
  ui.themeTa.addEventListener('input', () => {
    theme = ui.themeTa.value
    chrome.storage.local.set({ [STORAGE_KEYS.theme]: theme })
  })

  root.querySelector('.psx-clear').addEventListener('click', () => {
    selections = {}
    theme = ''
    ui.themeTa.value = ''
    chrome.storage.local.set({ [STORAGE_KEYS.sel]: selections, [STORAGE_KEYS.theme]: '' })
    renderGroups()
    renderPresetReset()
    toast(ui.shadow, '已清空')
  })

  ui.presetSel.addEventListener('change', () => {
    const key = ui.presetSel.value
    if (!key || !optionsData) return
    const p = optionsData.presets.find((x) => x.key === key)
    if (!p) return
    applySelections(p.selections)
    if (p.theme_hint && !theme) { theme = p.theme_hint; ui.themeTa.value = theme; persistSel() }
    renderGroups()
    toast(ui.shadow, `已应用：${p.label}`)
  })

  root.querySelector('.psx-inspire').addEventListener('click', doInspire)
  root.querySelector('.psx-generate').addEventListener('click', doGenerate)
}

function applySelections(sel) {
  selections = {}
  for (const [k, v] of Object.entries(sel || {})) selections[k] = Array.isArray(v) ? [...v] : v
  persistSel()
}

function persistSel() {
  chrome.storage.local.set({ [STORAGE_KEYS.sel]: selections, [STORAGE_KEYS.theme]: theme })
}

// ---------- 选项 / 预设 / 模型档位 ----------

async function loadOptions(force = false) {
  if (optionsData && !force) return
  const r = await api('/api/options')
  if (!r.ok) {
    ui.groups.innerHTML = `<div class="psx-empty">无法加载选项（${esc(r.error || r.status)}）<br>请确认本地服务已启动</div>`
    return
  }
  optionsData = r.data
  renderPresetReset()
  // 预设下拉
  for (const p of optionsData.presets || []) {
    const opt = document.createElement('option')
    opt.value = p.key
    opt.textContent = p.label
    ui.presetSel.appendChild(opt)
  }
  // 模型档位
  const models = optionsData.models || { llm_enabled: false, tiers: [] }
  ui.tierSel.innerHTML = ''
  for (const t of models.tiers || [{ id: 'default', label: '默认' }]) {
    const opt = document.createElement('option')
    opt.value = t.id
    opt.textContent = `模型：${t.label}`
    ui.tierSel.appendChild(opt)
  }
  if (!models.llm_enabled) {
    const opt = document.createElement('option')
    opt.value = 'default'
    opt.disabled = true
    ui.tierSel.insertBefore(opt, ui.tierSel.firstChild)
  }
  modelTier = ui.tierSel.value
  ui.tierSel.addEventListener('change', () => { modelTier = ui.tierSel.value })
  renderGroups()
}

function renderPresetReset() {
  if (!ui.presetSel) return
  ui.presetSel.value = ''
}

function renderGroups() {
  if (!optionsData) return
  ui.groups.innerHTML = ''
  for (const [gid, g] of Object.entries(optionsData.groups)) {
    const wrap = document.createElement('div')
    wrap.className = 'psx-group'
    const head = document.createElement('div')
    head.className = 'psx-group-head'
    head.innerHTML = `<span class="psx-group-name">${esc(g.name)}</span><span class="psx-group-count psx-hidden"></span><span class="psx-group-arrow">▶</span>`
    const body = document.createElement('div')
    body.className = 'psx-group-body'
    wrap.append(head, body)
    ui.groups.appendChild(wrap)

    const countEl = head.querySelector('.psx-group-count')
    const syncCount = () => {
      const n = selectedCount(gid)
      countEl.textContent = `${n}`
      countEl.classList.toggle('psx-hidden', n === 0)
    }
    head.addEventListener('click', () => wrap.classList.toggle('open'))
    syncCount()

    for (const opt of g.options) {
      const chip = document.createElement('span')
      chip.className = 'psx-chip'
      chip.textContent = opt.label
      chip.dataset.label = opt.label
      chip.addEventListener('click', () => {
        if (g.multi) {
          const cur = Array.isArray(selections[gid]) ? [...selections[gid]] : []
          const i = cur.indexOf(opt.label)
          if (i >= 0) cur.splice(i, 1)
          else cur.push(opt.label)
          if (cur.length) selections[gid] = cur
          else delete selections[gid]
        } else {
          if (selections[gid] === opt.label) delete selections[gid]
          else {
            selections[gid] = opt.label
            // 用途场景联动推荐画幅
            if (gid === 'usage' && opt.ratio) selections.ratio = opt.ratio
          }
        }
        persistSel()
        syncGroupChips(body, gid)
        syncCount()
      })
      body.appendChild(chip)
    }
    syncGroupChips(body, gid)
  }
}

function syncGroupChips(body, gid) {
  const v = selections[gid]
  body.querySelectorAll('.psx-chip').forEach((chip) => {
    chip.classList.toggle('on', Array.isArray(v) ? v.includes(chip.dataset.label) : v === chip.dataset.label)
  })
}

// ---------- 灵感主题 ----------

async function doInspire() {
  const btn = ui.shadow.querySelector('.psx-inspire')
  btn.disabled = true
  btn.textContent = '灵感中…'
  const r = await api('/api/inspire-theme', 'POST', { selections, theme, model_tier: modelTier })
  btn.disabled = false
  btn.textContent = '🎲 灵感'
  if (!r.ok) { toast(ui.shadow, '灵感生成失败'); return }
  const themes = r.data?.themes || []
  ui.themeSuggest.innerHTML = ''
  ui.themeSuggest.classList.toggle('psx-hidden', !themes.length)
  for (const t of themes) {
    const chip = document.createElement('span')
    chip.className = 'psx-chip'
    chip.textContent = t
    chip.addEventListener('click', () => {
      theme = t
      ui.themeTa.value = t
      persistSel()
      ui.themeSuggest.classList.add('psx-hidden')
    })
    ui.themeSuggest.appendChild(chip)
  }
}

// ---------- 生成（SSE 流，content script 直连） ----------

async function sseGenerate(path, body, nodes) {
  generating = true
  setGenButtons()
  ui.steps.innerHTML = ''
  ui.resultWrap.innerHTML = ''
  const stepEls = {}
  for (const node of nodes) {
    const el = document.createElement('div')
    el.className = 'psx-step'
    el.textContent = NODE_LABELS[node] || node
    ui.steps.appendChild(el)
    stepEls[node] = el
  }

  const showFatal = (msg) => {
    const box = document.createElement('div')
    box.className = 'psx-error-box'
    box.textContent = msg
    ui.resultWrap.appendChild(box)
  }

  try {
    const resp = await fetch(settings.serverUrl + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!resp.ok || !resp.body) throw new Error(`请求失败：${resp.status}`)

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fatal = null

    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() ?? ''
      for (const block of blocks) {
        let event = ''
        let data = ''
        for (const line of block.split('\n')) {
          if (line.startsWith('event: ')) event = line.slice(7)
          else if (line.startsWith('data: ')) data = line.slice(6)
        }
        if (!event || !data) continue
        const ev = JSON.parse(data)
        if (event === 'step') {
          const el = stepEls[ev.node]
          if (el) el.className = `psx-step ${ev.status}`
        } else if (event === 'warn') {
          const w = document.createElement('div')
          w.className = 'psx-warn'
          w.textContent = `⚠ ${ev.message}`
          ui.steps.appendChild(w)
        } else if (event === 'result') {
          lastResult = ev
          renderResult()
        } else if (event === 'error') {
          fatal = ev.message || '生成失败'
        }
      }
    }
    if (fatal) showFatal(fatal)
  } catch (e) {
    showFatal(`连接中断：${e}（请确认本地服务是否在运行）`)
  } finally {
    generating = false
    setGenButtons()
  }
}

function setGenButtons() {
  ui.shadow.querySelector('.psx-generate').disabled = generating
}

function doGenerate() {
  sseGenerate('/api/generations', {
    selections,
    theme,
    mode: 'standard',
    model_tier: modelTier,
  }, GEN_NODES)
}

function doRefine(instruction) {
  if (!lastResult?.id || !instruction.trim()) return
  sseGenerate(`/api/generations/${lastResult.id}/refine`, {
    instruction: instruction.trim(),
    model_tier: modelTier,
  }, REFINE_NODES)
}

function renderResult() {
  if (!lastResult) return
  const r = lastResult
  ui.resultWrap.innerHTML = ''
  const box = document.createElement('div')
  box.className = 'psx-result'
  const warns = [...(r.warnings || []), ...(r.notes || [])]
    .slice(0, 4)
    .map((n) => `<div class="psx-warn">⚠ ${esc(n.message)}</div>`)
    .join('')
  box.innerHTML = `
    <div class="psx-result-meta">
      <span class="psx-badge">模型 ${esc(r.model || '默认')}</span>
      ${r.suggested_ratio ? `<span class="psx-badge">画幅 ${esc(r.suggested_ratio)}</span>` : ''}
    </div>
    ${warns}
    <div class="psx-prompt"></div>
    <div class="psx-result-actions">
      <button class="psx-btn primary psx-copy">📋 一键复制</button>
      <button class="psx-fb-btn psx-fb-up" title="出图好评">👍</button>
      <button class="psx-fb-btn psx-fb-down" title="出图差评">👎</button>
    </div>
    <div class="psx-refine-row">
      <input class="psx-input psx-refine-input" style="flex:1" placeholder="按指令修改，如：改成夜景">
      <button class="psx-btn psx-refine-btn">迭代</button>
    </div>
  `
  box.querySelector('.psx-prompt').textContent = r.prompt
  ui.resultWrap.appendChild(box)

  box.querySelector('.psx-copy').addEventListener('click', async (e) => {
    const ok = await copyText(r.prompt)
    toast(ui.shadow, ok ? '已复制，去即梦粘贴吧' : '复制失败')
    if (ok) e.target.textContent = '✅ 已复制'
    setTimeout(() => { const b = box.querySelector('.psx-copy'); if (b) b.textContent = '📋 一键复制' }, 1500)
  })
  box.querySelector('.psx-fb-up').addEventListener('click', (e) => sendFeedback(r.id, 1, e.target))
  box.querySelector('.psx-fb-down').addEventListener('click', (e) => sendFeedback(r.id, -1, e.target))
  box.querySelector('.psx-refine-btn').addEventListener('click', () => {
    doRefine(box.querySelector('.psx-refine-input').value)
  })
  box.querySelector('.psx-refine-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doRefine(e.target.value)
  })
}

async function sendFeedback(id, rating, el) {
  await api(`/api/generations/${id}/feedback`, 'POST', { rating })
  const box = el.closest('.psx-result')
  box.querySelectorAll('.psx-fb-btn').forEach((b) => b.classList.remove('on'))
  el.classList.add('on')
  toast(ui.shadow, '已记录出图反馈')
}

// ---------- 历史 ----------

let historyLoaded = false

async function loadHistory() {
  const root = ui.panel.querySelector('.psx-tab-hist')
  if (!historyLoaded) root.innerHTML = '<div class="psx-empty">加载中…</div>'
  const r = await api('/api/generations?limit=20')
  if (!r.ok) { root.innerHTML = `<div class="psx-empty">加载失败（${esc(r.error || r.status)}）</div>`; return }
  historyLoaded = true
  const items = r.data || []
  if (!items.length) { root.innerHTML = '<div class="psx-empty">还没有生成记录</div>'; return }

  root.innerHTML = ''
  const refresh = document.createElement('div')
  refresh.className = 'psx-row'
  refresh.innerHTML = '<button class="psx-btn ghost psx-hist-refresh">↻ 刷新</button>'
  root.appendChild(refresh)
  refresh.querySelector('.psx-hist-refresh').addEventListener('click', () => { historyLoaded = false; loadHistory() })

  for (const it of items) {
    const el = document.createElement('div')
    el.className = 'psx-hist-item'
    const time = (it.created_at || '').replace('T', ' ').slice(5, 16)
    el.innerHTML = `
      <div class="psx-hist-meta">
        <span class="psx-hist-time">${esc(time)}</span>
        ${it.mode !== 'standard' ? `<span class="psx-badge">${esc(it.mode)}</span>` : ''}
        <button class="psx-btn ghost psx-hist-copy" style="padding:3px 10px">复制</button>
      </div>
      <div class="psx-hist-theme">${esc(it.theme || '（无主题）')}</div>
      <div class="psx-hist-prompt"></div>
    `
    el.querySelector('.psx-hist-prompt').textContent = it.final_prompt
    el.addEventListener('click', (e) => {
      if (e.target.closest('button')) return
      el.classList.toggle('open')
    })
    el.querySelector('.psx-hist-copy').addEventListener('click', async () => {
      const ok = await copyText(it.final_prompt)
      toast(ui.shadow, ok ? '已复制' : '复制失败')
    })
    root.appendChild(el)
  }
}

// ---------- 显隐控制 ----------

function showPanel(visible) {
  panelVisible = visible
  ui.panel.classList.toggle('psx-hidden', !visible)
  // 面板打开时藏起悬浮球；自动激活关闭时两者都藏
  ui.fab.classList.toggle('psx-hidden', visible || !settings.autoActivate)
}

init()
