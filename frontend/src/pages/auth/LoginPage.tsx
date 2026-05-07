import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link } from 'react-router-dom'
import { CircleNotch } from '@phosphor-icons/react'
import { Logo } from '@/components/common/Logo'
import { FormField } from '@/components/common/FormField'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { loginSchema, type LoginInput } from '@/features/auth/schemas'
import { useAuth } from '@/features/auth/useAuth'
import { ApiError, ValidationError } from '@/lib/api-client'
import { routes } from '@/constants/routes'

export default function LoginPage() {
  const { login } = useAuth()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur',
    defaultValues: { email: '', password: '' },
  })

  const isPending = login.isPending || isSubmitting

  const onSubmit = (data: LoginInput) => {
    login.mutate(data, {
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
        if (err instanceof ApiError && err.status === 401) {
          setError('root', { message: 'Не подошёл email или пароль. Проверь и попробуй ещё раз.' })
          return
        }
        setError('root', {
          message: 'Не удалось дозвониться до сервера. Проверь соединение и попробуй через минуту.',
        })
      },
    })
  }

  return (
    <div className="mx-auto flex max-w-[400px] flex-col px-[var(--space-xl)] pt-[clamp(64px,18vh,200px)] pb-[var(--space-3xl)]">
      <Logo className="mb-[var(--space-2xl)]" />

      <h1 className="mb-[var(--space-xl)] font-serif text-[length:var(--text-2xl)] font-semibold text-[color:var(--color-text)]">
        Войти
      </h1>

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

        <FormField id="password" label="Пароль" error={errors.password?.message}>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            disabled={isPending}
            aria-invalid={errors.password ? true : undefined}
            aria-describedby={errors.password ? 'password-error' : undefined}
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
              Заходим...
            </>
          ) : (
            'Войти'
          )}
        </Button>
      </form>

      <p className="mt-[var(--space-xl)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
        Нет аккаунта?{' '}
        <Link
          to={routes.register}
          className="font-medium text-[color:var(--color-primary)] underline-offset-4 hover:underline focus-visible:underline"
        >
          Зарегистрируйся
        </Link>
      </p>
    </div>
  )
}
