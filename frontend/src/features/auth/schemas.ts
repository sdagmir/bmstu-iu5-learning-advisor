import { z } from 'zod'

const emailField = z.string().email('Введи email в формате имя@домен.ру')

export const loginSchema = z.object({
  email: emailField,
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
