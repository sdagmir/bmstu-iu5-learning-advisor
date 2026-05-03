import { z } from 'zod'

/**
 * Email — стандартный валидатор zod с русским сообщением.
 * Бэк дополнительно валидирует строже (`pydantic[email]`), мы тут даём UX-подсказку.
 */
const emailField = z.string().email('Введи email в формате имя@домен.ру')

export const loginSchema = z.object({
  email: emailField,
  /**
   * Для логина не enforce'им длину: вдруг есть аккаунты со старыми паролями
   * нестандартной длины. Если пусто — словишь backend 401, это ок.
   */
  password: z.string().min(1, 'Введи пароль'),
})

export const registerSchema = z.object({
  email: emailField,
  password: z
    .string()
    .min(8, 'Пароль должен быть не короче 8 символов')
    .max(128, 'Слишком длинный пароль (макс. 128 символов)'),
})

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
