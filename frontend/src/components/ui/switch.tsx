import * as React from "react"
import { Switch as SwitchPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"

/**
 * Шадсиновский Switch с явными `data-[state=...]:` селекторами.
 * Короткая форма `data-checked:` в этой связке Tailwind v4 + Radix UI
 * не отрабатывала (Radix ставит `data-state="checked"`, а Tailwind
 * `data-checked:` ищет boolean-атрибут `[data-checked]`).
 *
 * Дополнительно: unchecked-фон тонируем `border-strong/50` — на муть-подложках
 * (sandbox-aside) дефолтный `bg-input` сливался и казался невидимым.
 */
function Switch({
  className,
  size = "default",
  ...props
}: React.ComponentProps<typeof SwitchPrimitive.Root> & {
  size?: "sm" | "default"
}) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      data-size={size}
      className={cn(
        "peer group/switch relative inline-flex shrink-0 items-center rounded-full border transition-all outline-none after:absolute after:-inset-x-3 after:-inset-y-2 focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:ring-3 aria-invalid:ring-destructive/20",
        "data-[size=default]:h-[18.4px] data-[size=default]:w-[32px]",
        "data-[size=sm]:h-[14px] data-[size=sm]:w-[24px]",
        "data-[state=checked]:border-[color:var(--color-primary)] data-[state=checked]:bg-[color:var(--color-primary)]",
        "data-[state=unchecked]:border-[color:var(--color-border-strong)] data-[state=unchecked]:bg-[color:var(--color-border-strong)]/40",
        "data-[disabled]:cursor-not-allowed data-[disabled]:opacity-50",
        className
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className={cn(
          "pointer-events-none block rounded-full bg-[color:var(--color-surface)] shadow-sm ring-0 transition-transform",
          "group-data-[size=default]/switch:size-4",
          "group-data-[size=sm]/switch:size-3",
          // checked: бегунок справа
          "group-data-[size=default]/switch:data-[state=checked]:translate-x-[calc(100%-2px)]",
          "group-data-[size=sm]/switch:data-[state=checked]:translate-x-[calc(100%-2px)]",
          // unchecked: бегунок слева
          "group-data-[size=default]/switch:data-[state=unchecked]:translate-x-0",
          "group-data-[size=sm]/switch:data-[state=unchecked]:translate-x-0"
        )}
      />
    </SwitchPrimitive.Root>
  )
}

export { Switch }
