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
  const [reviewQueue, setReviewQueue] = useState([])
  const [reviewLoading, setReviewLoading] = useState(false)
  const [justifications, setJustifications] = useState({})
  const [fraudFlags, setFraudFlags] = useState([])

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
    fetchReviewQueue()
    fetchFraudFlags()
  }
  const fetchReviewQueue = async () => {
    setReviewLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/tender/${tenderId}/needs-review`)
      setReviewQueue(res.data.items)
    } catch (err) {
      alert('Error fetching review queue: ' + err.message)
    }
    setReviewLoading(false)
  }
const fetchFraudFlags = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tender/${tenderId}/fraud-check`)
      setFraudFlags(res.data.flags)
    } catch (err) {
      console.error('Error fetching fraud flags:', err.message)
    }
  }
  const downloadAuditReport = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tender/${tenderId}/audit-report`)
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `clearbid_audit_report_tender_${tenderId}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Error downloading report: ' + err.message)
    }
  }
  const handleReviewAction = async (verdictId, action) => {
    const justification = justifications[verdictId]
    if (!justification || justification.trim() === '') {
      alert('Justification is required before recording a decision.')
      return
    }

    const formData = new FormData()
    formData.append('action', action)
    formData.append('justification', justification)

    try {
      await axios.post(`${API_BASE}/review-decision/${verdictId}`, formData)
      setReviewQueue(prev => prev.filter(item => item.verdict_id !== verdictId))
    } catch (err) {
      alert('Error recording decision: ' + err.message)
    }
  }

  const handleJustificationChange = (verdictId, value) => {
    setJustifications(prev => ({ ...prev, [verdictId]: value }))
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
      {fraudFlags.length > 0 && (
        <div className="card fraud-section">
          <h2>⚠ Fraud Signals Detected</h2>
          <p className="hint">
            The system detected the following cross-bidder relationships. These require officer attention before final award decisions.
          </p>
          {fraudFlags.map((flag, idx) => (
            <div key={idx} className="fraud-flag">
              <span className="fraud-type">{flag.type.replace('_', ' ')}</span>
              <p>{flag.detail}</p>
            </div>
          ))}
        </div>
      )}
      {reviewLoading && <p className="hint">Loading review queue...</p>}

      {reviewQueue.length > 0 && (
        <div className="card review-section">
          <h2>Officer Review Queue</h2>
          <p className="hint">
            The following items require manual review. Each decision requires a written justification.
          </p>

          {reviewQueue.map((item) => (
            <div key={item.verdict_id} className="review-item">
              <div className="review-header">
                <span className="review-bidder">{item.bidder_filename}</span>
                <span className="review-criterion">{item.criterion_name}</span>
              </div>

              <div className="review-body">
                <div className="verdict-row">
                  <span className="label">Extracted value:</span>
                  <span>{item.extracted_value !== 'null' ? item.extracted_value : '—'}</span>
                </div>
                {item.source_page && (
                  <div className="verdict-row">
                    <span className="label">Source page:</span>
                    <span>{item.source_page}</span>
                  </div>
                )}
                {item.raw_snippet && (
                  <div className="verdict-row">
                    <span className="label">Evidence:</span>
                    <span className="snippet">"{item.raw_snippet}"</span>
                  </div>
                )}
                <div className="verdict-row reason">
                  <span className="label">Why flagged:</span>
                  <span>{item.reason}</span>
                </div>
              </div>

              <textarea
                className="justification-input"
                placeholder="Enter justification for your decision (required)..."
                value={justifications[item.verdict_id] || ''}
                onChange={(e) => handleJustificationChange(item.verdict_id, e.target.value)}
              />

              <div className="review-actions">
                <button
                  className="action-btn approve"
                  onClick={() => handleReviewAction(item.verdict_id, 'APPROVED')}
                >
                  Approve
                </button>
                <button
                  className="action-btn reject"
                  onClick={() => handleReviewAction(item.verdict_id, 'REJECTED')}
                >
                  Reject
                </button>
                <button
                  className="action-btn clarify"
                  onClick={() => handleReviewAction(item.verdict_id, 'CLARIFICATION_REQUESTED')}
                >
                  Request Clarification
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!reviewLoading && reviewQueue.length === 0 && bidders.length > 0 && (
    
        <div className="card">
          <p className="approved-msg">✓ No items pending review. All evaluations complete.</p>
        </div>
      )}
      {bidders.length > 0 && (
        <div className="card audit-section">
          <h2>Audit Trail</h2>
          <p className="hint">
            Download the complete decision record for this tender — every criterion,
            extracted value, source, confidence score, verdict, and officer action with timestamps.
          </p>
          <button className="approve-btn" onClick={downloadAuditReport}>
            Download Audit Report (JSON)
          </button>
        </div>
      )}
    </div>
  )
}

export default App