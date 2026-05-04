import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react'

/**
 * Тонкая обёртка над `useState` с записью в `sessionStorage` (по умолчанию)
 * или `localStorage`. Подходит для UI-состояний, которые раздражает терять
 * при навигации между экранами:
 *   - история чата
 *   - заполненный профиль симулятора / sandbox'а
 *   - выбранный пресет
 *
 * Что НЕ стоит сюда класть: формы (должны ресетиться), sensitive-данные
 * (используй authStore для токенов), серверные данные (TanStack Query сам
 * кэширует через memory).
 *
 * Семантика:
 *   - На mount читаем из storage; если парсинг провалился — берём `defaultValue`
 *   - На каждое обновление — пишем в storage. Запись на ПЕРВЫЙ рендер
 *     пропускаем, чтобы не перезаписать восстановленное значение тем же
 *     значением (defensive против race на сериализацию)
 *
 * Тип `T` сериализуется через JSON — не пихай функции, Map, Set.
 */
export function usePersistentState<T>(
  key: string,
  defaultValue: T,
  storage: Storage = sessionStorage,
): [T, Dispatch<SetStateAction<T>>] {
  const [state, setState] = useState<T>(() => {
    try {
      const stored = storage.getItem(key)
      if (stored !== null) return JSON.parse(stored) as T
    } catch {
      // повреждённый JSON — игнорируем, идём на default
    }
    return defaultValue
  })

  // Не пишем при первом рендере — чтобы не затереть свежечитанное значение
  // тем же сериализованным значением (косметическая оптимизация).
  const isInitialRender = useRef(true)
  useEffect(() => {
    if (isInitialRender.current) {
      isInitialRender.current = false
      return
    }
    try {
      storage.setItem(key, JSON.stringify(state))
    } catch {
      // QuotaExceeded или storage недоступен (приватный режим Safari) —
      // тихо игнорируем, чтобы не ломать UI
    }
  }, [key, state, storage])

  return [state, setState]
}
