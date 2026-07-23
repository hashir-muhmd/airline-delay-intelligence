import { useState } from 'react'
import { ComposableMap, Geographies, Geography, Marker, Line, ZoomableGroup } from 'react-simple-maps'
import './RouteMap.css'

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

function RouteMap({ hub, destinations }) {
  const [hovered, setHovered] = useState(null)
  const [zoom, setZoom] = useState(1)
  const hubCoords = [hub.longitude, hub.latitude]

  const zoomIn = () => setZoom((z) => Math.min(z * 1.5, 8))
  const zoomOut = () => setZoom((z) => Math.max(z / 1.5, 1))
  const resetZoom = () => setZoom(1)

  return (
    <div className="route-map-wrap">
      <div className="route-map-legend">
        <span className="route-map-legend-item">
          <span className="route-map-legend-dot route-map-legend-dot-hub" /> DOH hub
        </span>
        <span className="route-map-legend-item">
          <span className="route-map-legend-dot route-map-legend-dot-dest" /> Connected airport
        </span>
        <span className="route-map-legend-note">{destinations.length} routes</span>
      </div>

      <div className="route-map-canvas">
        <ComposableMap
          projection="geoEqualEarth"
          projectionConfig={{ scale: 175, center: [30, 15] }}
          width={800}
          height={420}
          className="route-map-svg"
        >
          <ZoomableGroup zoom={zoom} center={hubCoords} minZoom={1} maxZoom={8}>
            <Geographies geography={GEO_URL}>
              {({ geographies }) =>
                geographies.map((geo) => (
                  <Geography key={geo.rsmKey} geography={geo} className="route-map-country" />
                ))
              }
            </Geographies>

            {destinations.map((d) => (
              <Line
                key={`line-${d.code}`}
                from={hubCoords}
                to={[d.longitude, d.latitude]}
                className={`route-map-arc ${hovered === d.code ? 'route-map-arc-active' : ''}`}
              />
            ))}

            {destinations.map((d) => (
              <Marker
                key={`marker-${d.code}`}
                coordinates={[d.longitude, d.latitude]}
                onMouseEnter={() => setHovered(d.code)}
                onMouseLeave={() => setHovered(null)}
              >
                <circle
                  r={hovered === d.code ? 5 / zoom : 2.5 / zoom}
                  className={`route-map-point ${hovered === d.code ? 'route-map-point-active' : ''}`}
                />
                {hovered === d.code && (
                  <g>
                    <rect
                      x={8 / zoom}
                      y={-20 / zoom}
                      width={(d.code.length + d.city.length + 4) * (6.2 / zoom)}
                      height={18 / zoom}
                      rx={4 / zoom}
                      className="route-map-label-bg"
                    />
                    <text
                      x={14 / zoom}
                      y={-7 / zoom}
                      className="route-map-label"
                      style={{ fontSize: `${11 / zoom}px` }}
                    >
                      {d.code} · {d.city}
                    </text>
                  </g>
                )}
              </Marker>
            ))}

            <Marker coordinates={hubCoords}>
              <circle r={9 / zoom} className="route-map-hub-ring" />
              <circle r={4 / zoom} className="route-map-hub-dot" />
              <rect
                x={14 / zoom}
                y={-22 / zoom}
                width={40 / zoom}
                height={18 / zoom}
                rx={4 / zoom}
                className="route-map-hub-label-bg"
              />
              <text
                x={20 / zoom}
                y={-9 / zoom}
                className="route-map-hub-label"
                style={{ fontSize: `${12 / zoom}px` }}
              >
                DOH
              </text>
            </Marker>
          </ZoomableGroup>
        </ComposableMap>

        <div className="route-map-zoom-controls">
          <button className="route-map-zoom-btn" onClick={zoomIn} aria-label="Zoom in">+</button>
          <button className="route-map-zoom-btn" onClick={zoomOut} aria-label="Zoom out">−</button>
          <button className="route-map-zoom-btn route-map-zoom-reset" onClick={resetZoom} aria-label="Reset zoom">⟲</button>
        </div>
      </div>
    </div>
  )
}

export default RouteMap