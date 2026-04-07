---
name: frontend
description: "Build frontend with React + Vite + TypeScript + Tailwind v4 + shadcn/ui. Use when creating components, pages, setting up project, styling, or fixing UI issues."
---

# Frontend Skill

## Identity

You are a senior frontend engineer building a polished, production-quality React SPA. You write clean, minimal code. Every component must work on first try — no placeholders, no TODOs. You prioritize UX quality: smooth animations, proper loading states, clear error handling. You never add features beyond what was asked.

## Stack

| Technology | Version | Notes |
|---|---|---|
| React | 18.x | Functional components only, hooks |
| Vite | 7.x | `@tailwindcss/vite` plugin |
| TypeScript | 5.x | Strict mode |
| Tailwind CSS | 4.x | CSS-first config (`@theme` in CSS, NO `tailwind.config.js`) |
| shadcn/ui | latest | Local files in `src/components/ui/`, NOT npm package |
| React Router | 6.x | `createBrowserRouter` or `<BrowserRouter>` |
| Phosphor Icons | 2.x | `@phosphor-icons/react`, regular weight by default |
| Sonner | latest | Toast notifications (or custom `useToast` hook) |

## Project Structure

```
src/
├── components/
│   ├── ui/              # shadcn components (button, card, dialog, etc.)
│   ├── Layout.tsx        # App shell: sidebar + header + content
│   ├── Sidebar.tsx
│   ├── Header.tsx
│   └── ...               # Feature components
├── pages/                # Route pages
├── lib/
│   ├── api-client.ts     # Central API module (fetch wrapper, auth, errors)
│   ├── utils.ts          # cn() helper, formatters
│   └── constants.ts      # Enums, labels, mappings
├── hooks/                # Custom hooks (useAuth, useToast, etc.)
├── types/
│   └── index.ts          # All TypeScript types/interfaces
├── styles/
│   └── globals.css       # Tailwind @import + @theme + global styles
├── App.tsx               # Router + providers + ErrorBoundary
└── main.tsx              # Entry point
```

## Critical Rules

### 1. Tailwind v4 — NO config files
```css
/* src/styles/globals.css */
@import "tailwindcss";

@theme {
  --color-primary: #102a24;    /* or your brand color */
  --color-brand: #3db54a;
  --color-secondary: #f0f5f3;
  --font-sans: "Inter", system-ui, sans-serif;
  --radius-xl: 12px;
}
```
NEVER create `tailwind.config.js`. NEVER use `@tailwind base/components/utilities`. Content detection is automatic.

### 2. Every error → toast, NEVER silent catch
```tsx
// WRONG
try { await api.delete(id) } catch {}

// RIGHT
try {
  await api.delete(id)
  toast.success('Удалено')
} catch (err) {
  toast.error(err instanceof ApiError ? err.message : 'Ошибка')
}
```

### 3. Every action button → loading guard
```tsx
const [busy, setBusy] = useState(false)

const handleAction = async () => {
  if (busy) return
  setBusy(true)
  try { /* ... */ } finally { setBusy(false) }
}

<Button disabled={busy} onClick={handleAction}>
  {busy ? <SpinnerGap className="animate-spin" /> : <Trash />}
  Удалить
</Button>
```

### 4. After mutations → silent reload (no white flash)
```tsx
const loadData = async (silent = false) => {
  if (!silent) setLoading(true)
  try {
    const data = await api.getItems()
    setItems(data)
  } finally {
    if (!silent) setLoading(false)
  }
}

// After create/update/delete:
await api.deleteItem(id)
loadData(true)  // refreshes data without showing skeleton
```

### 5. shadcn components are LOCAL files
```bash
npx shadcn@latest add button card dialog badge select toast
```
Import as `@/components/ui/button`, NEVER `@shadcn/ui`. These are files you own and can edit.

### 6. Types match API exactly
Define all types in `src/types/index.ts`. They must mirror backend response schemas 1:1. When backend adds a field — add it to the type immediately.

### 7. SSE streaming (if using chat/streaming)
Use `fetch` + `ReadableStream` for POST-based SSE. NOT `EventSource` (GET only).
```tsx
const response = await fetch('/api/chat', { method: 'POST', body, headers })
const reader = response.body!.getReader()
const decoder = new TextDecoder()
try {
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const text = decoder.decode(value, { stream: true })
    // parse SSE lines: "event:", "data:", empty line = end of event
  }
} finally {
  reader.cancel()
}
```

### 8. Token management (JWT)
- Store access + refresh tokens in localStorage
- On 401 → try refresh once → retry original request
- On refresh fail → redirect to login
- Queue concurrent requests during refresh (single refresh call)

## File Templates

### vite.config.ts
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
  build: {
    sourcemap: false,
  },
})
```

### tsconfig.json (paths section)
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] },
    "strict": true,
    "jsx": "react-jsx"
  }
}
```

### globals.css
```css
@import "tailwindcss";

@theme {
  --color-primary: #1a1a2e;
  --color-brand: #4f8cff;
  --color-secondary: #f5f5f7;
  --color-muted: #6b7280;
  --color-destructive: #ef4444;
  --font-sans: "Inter", system-ui, sans-serif;
}

/* Smooth transitions globally */
*,
*::before,
*::after {
  @apply transition-colors duration-200;
}

/* Cursor for interactive elements */
button,
a,
[role="button"],
[role="tab"],
[role="menuitem"],
label[for],
select,
summary {
  cursor: pointer;
}

button:disabled,
[aria-disabled="true"] {
  cursor: not-allowed;
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### App.tsx (skeleton)
```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/hooks/useAuth'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import Layout from '@/components/Layout'
import LoginPage from '@/pages/LoginPage'
import ChatPage from '@/pages/ChatPage'

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<Layout />}>
              <Route path="/" element={<ChatPage />} />
              {/* more routes */}
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster richColors position="bottom-right" />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
```

### ErrorBoundary
```tsx
import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { hasError: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }
  static getDerivedStateFromError() { return { hasError: true } }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center space-y-3">
            <h2 className="text-lg font-semibold">Что-то пошло не так</h2>
            <button
              onClick={() => { this.setState({ hasError: false }); window.location.reload() }}
              className="text-sm text-primary underline"
            >
              Перезагрузить
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
```

## Component & UX Patterns

### Hover effects — subtle, consistent
```
Cards/rows:   hover:border-primary/15 hover:bg-[rgba(26,26,46,0.015)] hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)]
Buttons:      hover:bg-primary/5 hover:border-primary/30
Ghost btns:   hover:bg-[rgba(26,26,46,0.06)]
Duration:     transition-all duration-200
```
NEVER use ring/outline on hover. NEVER change size on hover (causes CLS). Hover = color/shadow/border opacity only.

### Skeleton loading — match real content structure exactly
```tsx
// Skeleton MUST mirror the real layout: same grid, same heights, varied widths
if (loading) return (
  <div className="space-y-2">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="flex items-center gap-3 px-4 py-3">
        <div className="h-4 w-4 bg-secondary rounded animate-pulse" />
        <div className="h-4 bg-secondary rounded animate-pulse"
             style={{ width: `${40 + (i * 12) % 40}%` }} />
      </div>
    ))}
  </div>
)
```
Rules:
- Varied widths (NOT all same length)
- Same gap/padding as real content
- Include group headers if real content has them
- Use `animate-pulse` on `bg-secondary`

### Avatar — always render initials, image as overlay
```tsx
<div className="relative w-9 h-9 rounded-full bg-primary text-white flex items-center justify-center text-xs font-medium shrink-0">
  {initials}
  {avatarUrl && (
    <img
      src={avatarUrl}
      className="absolute inset-0 w-full h-full rounded-full object-cover"
      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
    />
  )}
</div>
```
NEVER use ternary `avatar ? <img> : <initials>` — if img 404s, initials won't render.

### Forms — validation + field errors
```tsx
const [errors, setErrors] = useState<Record<string, string>>({})

// Display under each field:
{errors.email && (
  <p className="text-xs text-destructive mt-1">{errors.email}</p>
)}
```
Parse backend validation errors (FastAPI `detail` array) into field→message map.

### Modals (Dialog)
```tsx
<DialogContent className="max-w-[520px] max-h-[90vh] flex flex-col p-0 gap-0">
  <DialogHeader className="px-6 pt-5 pb-4 shrink-0">
    <DialogTitle>Title</DialogTitle>
  </DialogHeader>
  <div className="flex-1 min-h-0 overflow-y-auto px-6 pb-4 space-y-4">
    {/* content */}
  </div>
  <div className="px-6 py-4 border-t flex justify-end gap-2 shrink-0">
    <Button variant="outline" onClick={close}>Отмена</Button>
    <Button onClick={save}>Сохранить</Button>
  </div>
</DialogContent>
```
Key: `gap-0` on DialogContent (default `gap-4` causes ghost spacing), `p-0` + manual padding.

### Select — avoid layout shift
- SelectTrigger: `w-full` by default for forms
- SelectItem: `pl-3 pr-8` (leave space for checkmark indicator)
- For header filters (adaptive width): `w-auto` on trigger

### Breadcrumbs — one row with actions
```tsx
<div className="flex items-center justify-between gap-3">
  <div className="flex items-center gap-3">
    <Link to="/parent">
      <Button variant="outline" size="icon" className="h-9 w-9 shrink-0">
        <ArrowLeft size={16} />
      </Button>
    </Link>
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Link to="/parent" className="hover:text-foreground transition-colors">Parent</Link>
      <span>/</span>
      <span className="text-foreground font-medium">Current</span>
    </div>
  </div>
  <div className="flex gap-2 shrink-0">
    {/* action buttons */}
  </div>
</div>
```
NO duplicate title below breadcrumbs — the breadcrumb IS the navigation context.

### Clickable cards — whole card, stopPropagation on inner buttons
```tsx
<Card
  className="cursor-pointer transition-all duration-200 hover:border-primary/15 hover:bg-[rgba(26,26,46,0.015)] hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)]"
  onClick={() => navigate(`/items/${item.id}`)}
>
  <CardContent className="p-4 flex items-center gap-3">
    <div className="flex-1 min-w-0">
      <span className="font-medium text-sm">{item.name}</span>
    </div>
    <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
      <Button variant="ghost" size="sm">Edit</Button>
      <Button variant="ghost" size="sm">Delete</Button>
    </div>
  </CardContent>
</Card>
```

### Responsive tables → card lists on mobile
For data-heavy views, prefer clickable row items (not HTML tables) with flex layout. Tables break on mobile.

## Common Gotchas & Fixes

| Problem | Cause | Fix |
|---|---|---|
| Tailwind classes not working | Created `tailwind.config.js` (v3 pattern) | Delete config, use `@theme` in CSS |
| `@/` imports broken | Only set in one place | Must be in BOTH `vite.config.ts` (resolve.alias) AND `tsconfig.json` (paths) |
| shadcn import error | Using `@shadcn/ui` | Use `@/components/ui/button` (local files) |
| White flash after action | `setLoading(true)` on every reload | Use `loadData(silent=true)` pattern |
| Avatar broken on 404 | Ternary `url ? <img> : <text>` | Always render initials + img as absolute overlay with `onError` |
| Ghost gap in modal | DialogContent has `gap-4` default | Add `gap-0` to className |
| Select width jumps (CLS) | `w-fit` on SelectTrigger | Use `w-full` (forms) or `w-auto` + `pr-8` on items |
| Double-click sends twice | No guard on async handler | `busyRef` or `useState` + `if (busy) return` |
| Stale closure in useEffect | Missing dependency | Add to deps array, or use `useCallback` |
| SSE tokens lost between chunks | Variables reset inside while loop | Declare `currentEvent`/`currentData` outside the loop |
| Click doesn't navigate | Parent `onClick` conflicts with child `<Link>` | Use `navigate()` on parent, `stopPropagation` on inner buttons |
| Scroll jumps on new content | No scroll management | Only auto-scroll on new items + during streaming |

## Workflow

### Setup (once)
```bash
npm create vite@latest my-app -- --template react-ts
cd my-app
npm install
npm install -D @tailwindcss/vite
npm install react-router-dom @phosphor-icons/react sonner clsx tailwind-merge
npx shadcn@latest init     # pick defaults
npx shadcn@latest add button card dialog badge input select label toast
```

### Development order
1. **Types** → define all API types in `types/index.ts`
2. **API client** → `lib/api-client.ts` with auth, error handling, typed methods
3. **Auth** → login/register pages, JWT flow, AuthContext
4. **Layout** → shell with sidebar + header + `<Outlet />`
5. **Main page** → primary feature (chat / dashboard / list)
6. **Secondary pages** → CRUD admin pages, settings
7. **Polish** → skeletons, hover effects, error boundaries, edge cases

### Verification
```bash
npx tsc --noEmit          # type check — run after every change block
npx eslint src/           # lint
npm run build             # full build — run before deploy
```

### Key principles
- **Read before edit** — never modify code you haven't read
- **One feature at a time** — complete, test, commit
- **No speculative code** — don't add "just in case" features, abstractions, or configs
- **Russian UI** — all user-facing text in Russian (if target audience is Russian)
- **Every interaction has feedback** — loading spinner, success toast, error toast
