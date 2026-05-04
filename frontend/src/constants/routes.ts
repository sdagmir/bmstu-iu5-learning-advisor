/**
 * Типизированные пути приложения. Не городить строки в JSX —
 * только через этот объект, чтобы при рефакторе IDE находила все ссылки.
 */
export const routes = {
  login: '/login',
  register: '/register',
  onboarding: '/onboarding',
  home: '/',
  chat: '/chat',
  profile: '/profile',
  coverage: '/coverage',
  history: '/history',
  recommendation: (id: string) => `/recommendations/${id}`,
  dev: {
    cards: '/dev/cards',
  },
  admin: {
    root: '/admin',
    rules: '/admin/rules',
    simulator: '/admin/simulator',
    traces: '/admin/traces',
    catalog: (entity: string) => `/admin/catalog/${entity}`,
    knowledge: '/admin/knowledge',
    users: '/admin/users',
  },
} as const
