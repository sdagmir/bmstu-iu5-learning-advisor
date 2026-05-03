import { useEffect, useState } from 'react'

/**
 * Возвращает значение, обновляющееся не чаще `delay` мс после последнего изменения.
 * Используется для трекинга «спокойного» состояния формы (симулятор) перед
 * запуском дорогого запроса.
 */
export function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])

  return debounced
}
