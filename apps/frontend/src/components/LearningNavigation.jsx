import { Target, Route, BarChart3, History } from 'lucide-react'
import { NavLink } from '../router'
import './LearningNavigation.css'

const facets = [
  { path: '/learning/goals', label: '目标', icon: Target },
  { path: '/learning/plan', label: '路径', icon: Route },
  { path: '/learning/progress', label: '进展', icon: BarChart3 },
  { path: '/learning/history', label: '历史', icon: History },
]

export default function LearningNavigation() {
  return (
    <nav className="learning-navigation" aria-label="学习域导航">
      {facets.map((facet) => (
        <NavLink
          key={facet.path}
          to={facet.path}
          className="learning-navigation__item"
        >
          <facet.icon size={16} />
          <span>{facet.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
