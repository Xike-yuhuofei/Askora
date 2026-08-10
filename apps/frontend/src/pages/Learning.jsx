import { useEffect } from 'react'
import { useNavigate } from '../router'

export default function Learning() {
  const navigate = useNavigate()

  useEffect(() => {
    navigate('/learning/goals', { replace: true })
  }, [navigate])

  return null
}
