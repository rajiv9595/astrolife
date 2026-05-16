import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import '../styles/DeveloperAPI.css'

function DeveloperAPI({ userData }) {
  const [keys, setKeys] = useState([])
  const [newKeyName, setNewKeyName] = useState('')
  const [loading, setLoading] = useState(false)
  const [newlyCreatedKey, setNewlyCreatedKey] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchKeys()
  }, [])

  const fetchKeys = async () => {
    try {
      setLoading(true)
      const token = sessionStorage.getItem('token') || localStorage.getItem('token')
      const res = await fetch('http://localhost:8001/api-keys', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!res.ok) throw new Error('Failed to fetch API keys')
      const data = await res.json()
      setKeys(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateKey = async (e) => {
    e.preventDefault()
    if (!newKeyName.trim()) return

    try {
      setLoading(true)
      setError(null)
      const token = sessionStorage.getItem('token') || localStorage.getItem('token')
      const res = await fetch('http://localhost:8001/api-keys', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newKeyName })
      })
      if (!res.ok) throw new Error('Failed to create API key')
      const data = await res.json()
      setNewlyCreatedKey(data.key)
      setNewKeyName('')
      fetchKeys()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRevoke = async (id) => {
    if (!window.confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) return
    
    try {
      setLoading(true)
      setError(null)
      const token = sessionStorage.getItem('token') || localStorage.getItem('token')
      const res = await fetch(`http://localhost:8001/api-keys/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!res.ok) throw new Error('Failed to revoke API key')
      fetchKeys()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="developer-api-container">
      <h2>Developer API</h2>
      <p className="api-subtitle">
        Generate API keys to integrate our chartgenerator into your own applications.
      </p>

      {error && <div className="error-message">{error}</div>}

      <div className="api-section">
        <h3>Create New API Key</h3>
        <form onSubmit={handleCreateKey} className="create-key-form">
          <input
            type="text"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Key Name (e.g., Mobile App Production)"
            required
          />
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Creating...' : 'Create Secret Key'}
          </button>
        </form>

        {newlyCreatedKey && (
          <div className="new-key-alert">
            <h4>API Key Created!</h4>
            <p>Please copy this secret key and store it securely. You won't be able to see it again!</p>
            <div className="key-display">
              <code>{newlyCreatedKey}</code>
              <button 
                onClick={() => {
                  navigator.clipboard.writeText(newlyCreatedKey)
                  alert('Copied to clipboard!')
                }}
                className="btn-copy"
              >
                Copy
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="api-section">
        <h3>Your API Keys</h3>
        {keys.length === 0 ? (
          <p className="no-keys">You haven't generated any API keys yet.</p>
        ) : (
          <div className="keys-list">
            <div className="keys-header">
              <span>Name</span>
              <span>Prefix</span>
              <span>Created</span>
              <span>Last Used</span>
              <span>Actions</span>
            </div>
            {keys.map(key => (
              <div key={key.id} className="key-row">
                <span className="key-name">{key.name}</span>
                <span className="key-prefix"><code>{key.key_prefix}</code></span>
                <span className="key-date">{new Date(key.created_at).toLocaleDateString()}</span>
                <span className="key-date">{key.last_used ? new Date(key.last_used).toLocaleDateString() : 'Never'}</span>
                <span>
                  <button onClick={() => handleRevoke(key.id)} className="btn-danger btn-sm">Revoke</button>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="api-section docs-section">
        <h3>Quickstart Guide</h3>
        <div className="code-example">
          <h4>Endpoint: <code>POST https://yourlifepath.vercel.app/compute</code></h4>
          <pre>
            {`curl -X POST https://yourlifepath.vercel.app/compute \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: your_secret_api_key_here" \\
  -d '{
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "second": 0,
    "tz": "Asia/Kolkata",
    "lat": 28.6139,
    "lon": 77.2090
  }'`}
          </pre>
        </div>
      </div>
    </div>
  )
}

export default DeveloperAPI
