// 工具栏弹窗：服务地址 / 自动激活开关 / 手动唤起面板

const JIMENG_MATCH = 'https://jimeng.jianying.com/*'
const DEFAULT_SERVER = 'http://localhost:8100'

const $ = (id) => document.getElementById(id)
const serverInput = $('serverUrl')
const autoCb = $('autoActivate')

// ---------- 初始化读取 ----------

chrome.storage.local.get(['serverUrl', 'autoActivate']).then(({ serverUrl, autoActivate }) => {
  serverInput.value = serverUrl || DEFAULT_SERVER
  autoCb.checked = autoActivate !== false
})

checkHealth()

async function checkHealth() {
  const url = serverInput.value.trim() || DEFAULT_SERVER
  try {
    const resp = await fetch(`${url}/api/health`)
    setHealth(resp.ok)
  } catch {
    setHealth(false)
  }
}

function setHealth(ok) {
  $('dot').classList.toggle('ok', ok)
  $('statusText').textContent = ok ? '已连接' : '未连接'
}

// ---------- 保存 ----------

$('save').addEventListener('click', async () => {
  const url = serverInput.value.trim().replace(/\/+$/, '')
  if (!/^https?:\/\//.test(url)) {
    $('tip').textContent = '地址需以 http:// 或 https:// 开头'
    return
  }
  // 非默认地址需要用户授权对应域名的访问权限（host permission）
  if (![`${DEFAULT_SERVER}/*`, 'http://127.0.0.1:8100/*'].includes(`${url}/*`)) {
    try {
      const granted = await chrome.permissions.request({ origins: [`${url}/*`] })
      if (!granted) {
        $('tip').textContent = '未授权访问该地址，插件将无法连接服务'
        return
      }
    } catch {
      $('tip').textContent = '授权失败，请重试'
      return
    }
  }
  await chrome.storage.local.set({ serverUrl: url, autoActivate: autoCb.checked })
  $('tip').textContent = '已保存'
  checkHealth()
})

// ---------- 在当前即梦页唤起 / 收起面板 ----------

$('togglePanel').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  if (!tab?.id || !tab.url || !tab.url.startsWith('https://jimeng.jianying.com')) {
    $('tip').textContent = '请先打开即梦网站（jimeng.jianying.com）'
    return
  }
  await chrome.tabs.sendMessage(tab.id, { type: 'psx-set-visible', visible: 'toggle' })
  window.close()
})

$('openWorkbench').addEventListener('click', async () => {
  const url = serverInput.value.trim() || DEFAULT_SERVER
  const u = new URL(url)
  u.port = '5173' // 本地完整工作台（web 前端 dev server）
  await chrome.tabs.create({ url: u.origin })
})
