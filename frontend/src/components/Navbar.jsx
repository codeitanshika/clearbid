export default function Navbar({ onHome }) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand" onClick={onHome}>
          <span className="navbar-logo">⚖</span>
          <span className="navbar-title">ClearBid</span>
          <span className="navbar-subtitle">Procurement Intelligence</span>
        </div>
      </div>
    </nav>
  )
}