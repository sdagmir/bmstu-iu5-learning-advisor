/**
 * Русская плюрализация: вернёт правильную форму существительного в зависимости
 * от числа.
 *
 * @example
 * pluralize(1, 'правило', 'правила', 'правил')  // 'правило'
 * pluralize(2, 'правило', 'правила', 'правил')  // 'правила'
 * pluralize(5, 'правило', 'правила', 'правил')  // 'правил'
 * pluralize(11, 'правило', 'правила', 'правил') // 'правил' (исключение 11–14)
 */
export function pluralize(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return one
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few
  return many
}
