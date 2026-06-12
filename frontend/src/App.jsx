import { useState } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [tenderId, setTenderId] = useState(null)
  const [criteria, setCriteria] = useState([])
  const [approved, setApproved] = useState(false)
  const [loading, setLoading] = useState(false)
  const [bidderLoading, setBidderLoading] = useState(false)
  const [bidders, setBidders] = useState([])

  const handleTenderUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await axios.post(`${API_BASE}/upload-tender`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setTenderId(res.data.tender_id)
      setCriteria(res.data.criteria)
      setApproved(false)
      setBidders([])
    } catch (err) {
      alert('Error uploading tender: ' + err.message)
    }
    setLoading(false)
  }

  const handleApprove = async () => {
    try {
      await axios.post(`${API_BASE}/approve-tender/${tenderId}`)
      setApproved(true)
    } catch (err) {
      alert('Error approving: ' + err.message)
    }
  }

  const handleBidderUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    setBidderLoading(true)

    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('tender_id', tenderId)

      try {
        const res = await axios.post(`${API_BASE}/evaluate-bidder`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        setBidders(prev => [...prev, res.data])
      } catch (err) {
        alert(`Error evaluating ${file.name}: ` + err.message)
      }
    }

    setBidderLoading(false)
  }

  const verdictClass = (verdict) => {
    if (verdict === 'PASS') return 'verdict-pass'
    if (verdict === 'FAIL') return 'verdict-fail'
    return 'verdict-review'
  }

  const verdictLabel = (verdict) => {
    if (verdict === 'PASS') return 'PASS'
    if (verdict === 'FAIL') return 'FAIL'
    return 'NEEDS REVIEW'
  }

  return (
    <div className="container">
      <h1>ClearBid</h1>
      <p className="subtitle">AI-based tender evaluation platform</p>

      <div className="card">
        <h2>Step 1: Upload Tender Document</h2>
        <input type="file" accept=".pdf" onChange={handleTenderUpload} />
        {loading && <p>Extracting criteria...</p>}
      </div>

      {criteria.length > 0 && (
        <div className="card">
          <h2>Step 2: Review Extracted Criteria</h2>
          <p className="hint">
            Review the criteria below. Confirm before bidder evaluation begins.
          </p>

          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Mandatory</th>
                <th>Threshold</th>
                <th>Raw Text</th>
              </tr>
            </thead>
            <tbody>
              {criteria.map((c) => (
                <tr key={c.criterion_id}>
                  <td>{c.criterion_id}</td>
                  <td>{c.name}</td>
                  <td>{c.type}</td>
                  <td>{c.mandatory ? 'Yes' : 'No'}</td>
                  <td>{c.threshold ?? '-'}</td>
                  <td className="raw-text">{c.raw_text}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {!approved ? (
            <button className="approve-btn" onClick={handleApprove}>
              Confirm Criteria & Proceed
            </button>
          ) : (
            <p className="approved-msg">✓ Criteria approved. Tender ID: {tenderId}</p>
          )}
        </div>
      )}

      {approved && (
        <div className="card">
          <h2>Step 3: Upload Bidder Documents</h2>
          <p className="hint">
            Upload one or more bidder submission PDFs. Each will be evaluated against the approved criteria.
          </p>
          <input
            type="file"
            accept=".pdf"
            multiple
            onChange={handleBidderUpload}
          />
          {bidderLoading && <p>Evaluating bidder(s)...</p>}
        </div>
      )}

      {bidders.map((bidder) => (
        <div className="card" key={bidder.bidder_id}>
          <h2>Bidder: {bidder.bidder}</h2>
          <div className="verdict-grid">
            {bidder.verdicts.map((v) => (
              <div key={v.criterion_id} className={`verdict-box ${verdictClass(v.verdict)}`}>
                <div className="verdict-header">
                  <span className="verdict-criterion">{v.criterion_name}</span>
                  <span className={`verdict-badge ${verdictClass(v.verdict)}`}>
                    {verdictLabel(v.verdict)}
                  </span>
                </div>
                <div className="verdict-body">
                  <div className="verdict-row">
                    <span className="label">Extracted value:</span>
                    <span>{v.extracted_value !== null ? String(v.extracted_value) : '—'}</span>
                  </div>
                  {v.source_page && (
                    <div className="verdict-row">
                      <span className="label">Source page:</span>
                      <span>{v.source_page}</span>
                    </div>
                  )}
                  {v.raw_snippet && (
                    <div className="verdict-row">
                      <span className="label">Evidence:</span>
                      <span className="snippet">"{v.raw_snippet}"</span>
                    </div>
                  )}
                  <div className="verdict-row">
                    <span className="label">Confidence:</span>
                    <span>{Math.round((v.confidence || 0) * 100)}%</span>
                  </div>
                  <div className="verdict-row reason">
                    <span className="label">Reason:</span>
                    <span>{v.reason}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default App