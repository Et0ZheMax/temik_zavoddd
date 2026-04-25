import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const setToken = useAuthStore((s) => s.setToken)
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')

  const submit = async () => {
    try {
      const { data } = await api.post('/auth/login', { username, password })
      setToken(data.access_token)
      navigate('/')
    } catch {
      setError('Ошибка авторизации')
    }
  }

  return (
    <div className="mx-auto mt-10 max-w-sm p-4">
      <div className="card space-y-3">
        <h1 className="text-xl font-semibold">Вход</h1>
        <input className="w-full rounded-lg border p-3" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input type="password" className="w-full rounded-lg border p-3" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn btn-primary w-full" onClick={submit}>Войти</button>
      </div>
    </div>
  )
}
