export default function Spinner({ text }) {
  return (
    <div className="spinner-wrapper">
      <div className="spinner" />
      {text && <p className="spinner-text">{text}</p>}
    </div>
  )
}