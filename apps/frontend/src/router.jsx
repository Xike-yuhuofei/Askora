import { createContext, forwardRef, useCallback, useContext, useEffect, useMemo, useState } from 'react'

const RouterContext = createContext(null)

function readPathname() {
  const hash = window.location.hash.replace(/^#/, '')
  const pathname = hash.split('?')[0] || '/'
  return pathname.startsWith('/') ? pathname : `/${pathname}`
}

export function RouterProvider({ children }) {
  const [pathname, setPathname] = useState(readPathname)

  useEffect(() => {
    const update = () => setPathname(readPathname())
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [])

  const navigate = useCallback((to, options = {}) => {
    const nextHash = `#${to.startsWith('/') ? to : `/${to}`}`
    if (options.replace) {
      const nextURL = `${window.location.pathname}${window.location.search}${nextHash}`
      window.history.replaceState(null, '', nextURL)
      setPathname(readPathname())
    } else {
      window.location.hash = nextHash
    }
  }, [])

  const value = useMemo(() => ({ pathname, navigate }), [pathname, navigate])
  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>
}

export function useLocation() {
  const context = useContext(RouterContext)
  if (!context) throw new Error('useLocation must be used within RouterProvider')
  return { pathname: context.pathname }
}

export function useNavigate() {
  const context = useContext(RouterContext)
  if (!context) throw new Error('useNavigate must be used within RouterProvider')
  return context.navigate
}

export function Navigate({ to, replace = false }) {
  const navigate = useNavigate()
  useEffect(() => navigate(to, { replace }), [navigate, replace, to])
  return null
}

export const NavLink = forwardRef(function NavLink({ to, className, match = 'exact', children, ...props }, ref) {
  const { pathname } = useLocation()
  const active = match === 'prefix'
    ? pathname === to || pathname.startsWith(`${to}/`)
    : pathname === to
  const resolvedClassName = typeof className === 'function'
    ? className({ isActive: active })
    : `${className || ''}${active ? ' active' : ''}`.trim()

  return (
    <a ref={ref} href={`#${to}`} className={resolvedClassName} aria-current={active ? 'page' : undefined} {...props}>
      {children}
    </a>
  )
})
