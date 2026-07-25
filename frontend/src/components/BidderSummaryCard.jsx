export default function BidderSummaryCard({ bidder, onClick }) {
  const verdicts = bidder.verdicts || bidder.criteria_results || []

  const passed = verdicts.filter(v => v.verdict === 'PASS').length
  const failed = verdicts.filter(v => v.verdict === 'FAIL').length
  const review = verdicts.filter(v => v.verdict === 'NEEDS_REVIEW').length
  const total = verdicts.length

  const overallStatus = () => {
    const mandatoryFails = verdicts.filter(
      v => v.verdict === 'FAIL' && v.mandatory
    ).length
    if (mandatoryFails > 0) return 'FAIL'
    if (review > 0) return 'REVIEW'
    return 'PASS'
  }

  const status = overallStatus()
  const statusConfig = {
    PASS: { label: 'Eligible', className: 'summary-pass', icon: '✓' },
    FAIL: { label: 'Not Eligible', className: 'summary-fail', icon: '✗' },
    REVIEW: { label: 'Needs Review', className: 'summary-review', icon: '!' }
  }
  const config = statusConfig[status]

  return (
    <div className={`bidder-summary-card ${config.className}`} onClick={onClick}>
      <div className="summary-left">
        <div className={`summary-icon ${config.className}`}>{config.icon}</div>
        <div>
          <div className="summary-filename">{bidder.filename || bidder.bidder}</div>
          <div className="summary-counts">
            <span className="count-pass">{passed} passed</span>
            <span className="count-sep">·</span>
            <span className="count-fail">{failed} failed</span>
            {review > 0 && <>
              <span className="count-sep">·</span>
              <span className="count-review">{review} review</span>
            </>}
            <span className="count-sep">·</span>
            <span className="count-total">{total} total</span>
          </div>
        </div>
      </div>
      <div className={`summary-badge ${config.className}`}>
        {config.label}
      </div>
    </div>
  )
}