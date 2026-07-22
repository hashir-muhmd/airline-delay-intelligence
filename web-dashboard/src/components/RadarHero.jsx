import './RadarHero.css'

const blips = [
  { top: '30%', left: '62%', delay: '0s' },
  { top: '55%', left: '25%', delay: '1.4s' },
  { top: '70%', left: '68%', delay: '2.8s' },
  { top: '20%', left: '40%', delay: '0.7s' },
  { top: '45%', left: '78%', delay: '2.1s' },
]

function RadarHero() {
  return (
    <div className="radar-hero">
      <div className="radar-scope">
        <div className="radar-ring ring-1" />
        <div className="radar-ring ring-2" />
        <div className="radar-ring ring-3" />
        <div className="radar-ring ring-4" />
        <div className="radar-crosshair radar-crosshair-h" />
        <div className="radar-crosshair radar-crosshair-v" />
        <div className="radar-sweep" />
        {blips.map((b, i) => (
          <span
            key={i}
            className="radar-blip"
            style={{ top: b.top, left: b.left, animationDelay: b.delay }}
          />
        ))}
        <div className="radar-hub">
          <span className="radar-hub-code">DOH</span>
        </div>
      </div>
      <div className="radar-hero-text">
        <h1>SkyPulse</h1>
        <p>Live delay intelligence for Hamad International Airport</p>
      </div>
    </div>
  )
}

export default RadarHero