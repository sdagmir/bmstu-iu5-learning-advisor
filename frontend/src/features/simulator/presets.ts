import type { SimulatorProfile } from '@/types/api'

/**
 * Готовые профили для демо защиты — синтетические студенты с разными
 * сценариями. Каждый показывает другую часть логики ЭС.
 *
 * `user_id` — placeholder; для синтетического профиля бэк его игнорирует
 * для трейса, но требует валидный UUID-шейп.
 */

const FAKE_UUID = '00000000-0000-0000-0000-000000000000'

export interface Preset {
  id: string
  name: string
  description: string
  profile: SimulatorProfile
}

export const PRESETS: Preset[] = [
  {
    id: 'ml-novice-5',
    name: 'ML-новичок, 5 семестр',
    description: 'Цель ML, ничего по ML ещё не пройдено — система должна предложить ЦК',
    profile: {
      user_id: FAKE_UUID,
      semester: 5,
      career_goal: 'ml',
      technopark_status: 'none',
      workload_pref: 'normal',
      completed_ck_ml: false,
      ck_dev_status: 'no',
      completed_ck_security: false,
      completed_ck_testing: false,
      weak_math: false,
      weak_programming: false,
      coverage: 'low',
      ck_count_in_category: 'few',
    },
  },
  {
    id: 'first-sem',
    name: 'Первокурсник, без ТП',
    description: 'Только определяется с целью, минимум данных',
    profile: {
      user_id: FAKE_UUID,
      semester: 1,
      career_goal: 'undecided',
      technopark_status: 'none',
      workload_pref: 'light',
      completed_ck_ml: false,
      ck_dev_status: 'no',
      completed_ck_security: false,
      completed_ck_testing: false,
      weak_math: false,
      weak_programming: false,
      coverage: 'low',
      ck_count_in_category: 'few',
    },
  },
  {
    id: 'devops-7',
    name: 'DevOps, 7 семестр, активный',
    description: 'Цель DevOps, в Технопарке backend, ЦК по разработке частично',
    profile: {
      user_id: FAKE_UUID,
      semester: 7,
      career_goal: 'devops',
      technopark_status: 'backend',
      workload_pref: 'intensive',
      completed_ck_ml: false,
      ck_dev_status: 'partial',
      completed_ck_security: true,
      completed_ck_testing: true,
      weak_math: false,
      weak_programming: false,
      coverage: 'medium',
      ck_count_in_category: 'many',
    },
  },
  {
    id: 'weak-math-backend',
    name: 'Backend, слабая математика',
    description: 'Цель backend, средняя оценка по математике низкая — должно быть warning',
    profile: {
      user_id: FAKE_UUID,
      semester: 4,
      career_goal: 'backend',
      technopark_status: 'none',
      workload_pref: 'normal',
      completed_ck_ml: false,
      ck_dev_status: 'no',
      completed_ck_security: false,
      completed_ck_testing: false,
      weak_math: true,
      weak_programming: false,
      coverage: 'low',
      ck_count_in_category: 'few',
    },
  },
]
