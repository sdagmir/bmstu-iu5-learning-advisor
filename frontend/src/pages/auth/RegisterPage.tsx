import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link } from 'react-router-dom'
import { CircleNotch } from '@phosphor-icons/react'
import { Logo } from '@/components/common/Logo'
import { FormField } from '@/components/common/FormField'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { registerSchema, type RegisterInput } from '@/features/auth/schemas'
import { useAuth } from '@/features/auth/useAuth'
import { ApiError, ValidationError } from '@/lib/api-client'
import { routes } from '@/constants/routes'

export default function RegisterPage() {
  const { register: registerMut } = useAuth()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    mode: 'onBlur',
    defaultValues: { email: '', password: '' },
  })

  const isPending = registerMut.isPending || isSubmitting

  const onSubmit = (data: RegisterInput) => {
    registerMut.mutate(data, {
      onError: (err) => {
        if (err instanceof ValidationError) {
          for (const d of err.details) {
            const last = d.loc[d.loc.length - 1]
            if (last === 'email' || last === 'password') {
              setError(last, { message: d.msg })
            }
          }
          return
        }
        if (err instanceof ApiError && err.status === 409) {
          setError('email', { message: 'Этот email уже зарегистрирован. Войди вместо регистрации.' })
          return
        }
        setError('root', {
          message: 'Не удалось создать аккаунт. Проверь соединение и попробуй через минуту.',
        })
      },
    })
  }

  return (
    <div className="mx-auto flex max-w-[400px] flex-col px-[var(--space-xl)] pt-[clamp(64px,18vh,200px)] pb-[var(--space-3xl)]">
      <Logo className="mb-[var(--space-2xl)]" />

      <h1 className="mb-[var(--space-sm)] font-serif text-[length:var(--text-2xl)] font-semibold text-[color:var(--color-text)]">
        Создай аккаунт
      </h1>
      <p className="mb-[var(--space-xl)] text-[length:var(--text-base)] text-[color:var(--color-text-muted)]">
        Дальше — короткое знакомство, чтобы система подобрала рекомендации под твою цель.
      </p>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-col gap-[var(--space-base)]"
        noValidate
      >
        <FormField id="email" label="Email" error={errors.email?.message}>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            inputMode="email"
            spellCheck={false}
            autoFocus
            disabled={isPending}
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? 'email-error' : undefined}
            {...register('email')}
          />
        </FormField>

        <FormField
          id="password"
          label="Пароль"
          error={errors.password?.message}
          hint="Минимум 8 символов"
        >
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            disabled={isPending}
            aria-invalid={errors.password ? true : undefined}
            aria-describedby={
              errors.password ? 'password-error' : 'password-hint'
            }
            {...register('password')}
          />
        </FormField>

        {errors.root?.message && (
          <p
            role="alert"
            className="text-[length:var(--text-sm)] text-[color:var(--color-danger)]"
          >
            {errors.root.message}
          </p>
        )}

        <Button
          type="submit"
          disabled={isPending}
          className="mt-[var(--space-sm)] h-10 w-full text-[length:var(--text-base)]"
        >
          {isPending ? (
            <>
              <CircleNotch size={16} weight="regular" className="animate-spin" />
              Создаём аккаунт...
            </>
          ) : (
            'Создать аккаунт'
          )}
        </Button>
      </form>

      <p className="mt-[var(--space-xl)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
        Уже есть аккаунт?{' '}
        <Link
          to={routes.login}
          className="font-medium text-[color:var(--color-primary)] underline-offset-4 hover:underline focus-visible:underline"
        >
          Войди
        </Link>
      </p>
    </div>
  )
}
